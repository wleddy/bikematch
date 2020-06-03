from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString
from bikematch.models import Folks, Match

PRIMARY_TABLE = Match

mod = Blueprint('match',__name__, template_folder='templates/', url_prefix='/match',static_folder='static/')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Matches'


from shotglass2.takeabeltof.views import TableView

# this handles table list and record delete
@mod.route('/<path:path>',methods=['GET','POST',])
@mod.route('/<path:path>/',methods=['GET','POST',])
@mod.route('/',methods=['GET','POST',])
@table_access_required(PRIMARY_TABLE)
def display(path=None):
    # import pdb;pdb.set_trace()
    
    view = TableView(PRIMARY_TABLE,g.db)

    view.list_fields = [
            {'name':'id','label':'ID','class':'w3-hide-small','search':True},
            {'name':'match_date','search':'date'},
            {'name':'match_status',},
            {'name':'recipient_name','label':'Recipient'},
            {'name':'donor_name','label':'Donor'},
        ]
    
    # ON DELETE trigger in Match clears the match_id in Folks
    return view.dispatch_request()
    

## Edit the PRIMARY_TABLE
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)

    match = PRIMARY_TABLE(g.db)
    rec = None
    
    if rec_id == None:
        rec_id = request.form.get('id',request.args.get('id',-1))
        
    rec_id = cleanRecordID(rec_id)
    # import pdb;pdb.set_trace()

    if rec_id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    folks = Folks(g.db)
    recipients = folks.select(
        where=" lower(d_or_r) = 'recipient' and match_id is null",
        order_by = "full_name",
        )
    donors = folks.select(
        where=" lower(d_or_r) = 'donor' and match_id is null",
        order_by = "full_name",
        )
    donor = None
    recipient = None
    
    if rec_id == 0:
        rec = match.new()
        rec.match_date = local_datetime_now()
    else:
        rec = match.get(rec_id)
        if not rec:
            flash("Unable to locate that record")
            return redirect(g.listURL)
            
    if rec.id:
        #has a match
        donor = folks.get(rec.donor_id)
        recipient = folks.get(rec.recipient_id)

    if request.form:
        match.update(rec,request.form)
        if validForm(rec):
            match.save(rec)
            # Set the match id in the folks records
            for x in {rec.donor_id,rec.recipient_id}:
                temp_rec = folks.get(x)
                if temp_rec:
                    temp_rec.match_id = rec.id
                    temp_rec.status = "Matched"
                    folks.save(temp_rec)
                else:
                    g.db.rollback()
                    flash("Internal Error! Invalid Donor or Recipient id. (ID: {})".format(x))
                    return abort(500)
            
            g.db.commit()

            return redirect(g.listURL)

    # display form
    return render_template('match_edit.html', 
        rec=rec,
        donors=donors,
        recipients=recipients,
        donor=donor,
        recipient=recipient,
        )
    
    
def validForm(rec):
    # Validate the form
    valid_form = True
    
    test_id = cleanRecordID(rec.donor_id)
    if test_id < 1:
        valid_form = False
        flash("You must select a Donor")
    
    test_id = cleanRecordID(rec.recipient_id)
    if test_id < 1:
        valid_form = False
        flash("You must select a Recipient")
        
    if not rec.match_status.strip():
        valid_form = False
        flash("You must enter something the Status field")

    temp_date = getDatetimeFromString(rec.match_date.strip())
    if not temp_date:
        valid_form = False
        flash("The 'Match' date is not a valid date")
    else:
        rec.match_date = temp_date
        
        

    return valid_form
    

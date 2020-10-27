from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString
from shotglass2.takeabeltof.utils import looksLikeEmailAddress, formatted_phone_number
from bikematch.models import Match, Bike, Folks

PRIMARY_TABLE = Folks

mod = Blueprint('folks',__name__, template_folder='templates/folks', url_prefix='/folks',static_folder='static/')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Folks'


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
            {'name':'full_name','label':'Name'},
            {'name':'email',},
            {'name':'phone',},
        ]

    view.export_fields = None
        
    
    # ON DELETE trigger in Match clears the match_id in Recipient and Bike
    return view.dispatch_request()
    

## Edit the PRIMARY_TABLE
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)

    folks = PRIMARY_TABLE(g.db)
    rec = None
    # import pdb;pdb.set_trace()
    
    if rec_id == None:
        rec_id = request.form.get('id',request.args.get('id',-1))
        
    rec_id = cleanRecordID(rec_id)

    if rec_id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    new_rec = False
    if rec_id == 0:
        rec = folks.new()
        #create a stub record
        folks.save(rec,commit=True)
        g.cancelURL = g.deleteURL # so cancel is delete
        
    else:
        rec = folks.get(rec_id)
    
    if request.form:
        folks.update(rec,request.form)
        if validForm(rec):
            rec.phone = formatted_phone_number(rec.phone)
            folks.save(rec)


            folks.commit()

            return redirect(g.listURL)
    
    matches = Match(g.db).select(where="recipient_id = {}".format(rec.id),order_by="match_date DESC")    
    donations = Bike(g.db).select(where = "bike.id in (select bike_id from donor_bike where donor_id = {})".format(rec.id),order_by="created DESC")

    # display form
    return render_template('folks_edit.html', 
        rec=rec,
        matches=matches,
        donations=donations,
        )
    
    
@mod.route('/check_for_uniqe_email', methods=['POST',])
@mod.route('/check_for_uniqe_email/', methods=['POST',])
def check_for_uniqe_email():
    if request.form:
        id = request.form.get('id')
        email = request.form.get('email')
        if not email_is_unique(id,email):
            return "duplicate"
            
    return "Ok"
    
def email_is_unique(id,email):
    if id and email:
        recs = PRIMARY_TABLE(g.db).select(where="lower(email) = '{}' and id <> {}".format(email.strip().lower(),id.strip()))
        if recs:
            return False
    return True
    
    
def validForm(rec):
    # Validate the form
    valid_form = True
    
    if not rec.first_name.strip():
        flash("You must enter a first name")
        valid_form = False
        
    if not rec.last_name.strip():
        flash("You must enter a last name")
        valid_form = False
        
    if not rec.email.strip():
        flash("You must enter an email address")
        valid_form = False
    elif not looksLikeEmailAddress(rec.email.strip()):
        flash("'{}' doesn't look like an email address".format(rec.email))
        valid_form = False
        
    # recs = PRIMARY_TABLE(g.db).select(where="email = '{}' and id <> {}".format(rec.email,rec.id))
    if not email_is_unique(str(rec.id),str(rec.email)):
        flash("The email address '{}' is already in use.".format(rec.email))
        valid_form = False
        
        
    return valid_form
    

from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString
from bikematch.models import Match, Bike

PRIMARY_TABLE = Match

mod = Blueprint('match',__name__, template_folder='templates/match', url_prefix='/match',static_folder='static/')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Matches'


from shotglass2.takeabeltof.views import TableView, EditView

# this handles table list and record delete
@mod.route('/<path:path>',methods=['GET','POST',])
@mod.route('/<path:path>/',methods=['GET','POST',])
@mod.route('/',methods=['GET','POST',])
@table_access_required(PRIMARY_TABLE)
def display(path=None):
    # import pdb;pdb.set_trace()
    setExits()
    
    view = TableView(PRIMARY_TABLE,g.db)

    view.list_fields = [
            {'name':'id','label':'ID','class':'w3-hide-small','search':False},
            {'name':'match_date','search':'date'},
            {'name':'recipient_name','label':'Recipient'},
            {'name':'donor_name','label':'Donor'},
        ]
        
    view.export_fields = [
            {'name':'id','label':'Match ID',},
            {'name':'match_date','type':'date',},
            {'name':'recipient_id','label':'Recpient ID',},
            {'name':'recipient_name','label':'Recipient Name',},
            {'name':'recipient_email','label':'Recipient Email',},
            {'name':'recipient_phone','label':'Recipient Phone',},
            {'name':'payment_amt','default':0,},
            {'name':'donor_id','label':'Bike ID'},
            {'name':'donor_name','label':'Donor Name'},
            {'name':'donor_email','label':'Donor Email',},
            {'name':'donor_phone','label':'Donor Phone',},
        ]
        
    view.allow_record_addition = False
    
    return view.dispatch_request()
    

## Edit the PRIMARY_TABLE
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)
    
    view = EditView(PRIMARY_TABLE,g.db,rec_id)
    
    view.edit_fields = [
    {'name':'recipient_name','label':'Recipient','extras':'disabled',},
    {'name':'donor_name','label':'Donor','extras':'disabled',},
    {'name':'match_date','type':'date',},
    {'name':'payment_amt','default':0,},
    {'name':'match_comment','type':'textarea',},
    ]
    
    # import pdb;pdb.set_trace()
    view.update()
    
    if view.stay_on_form or not view.success:
        return view.render()
        
    return redirect(g.listURL)


    
def match_bike(folks_id,bike_id,payment_amt=0,match_date=None):
    """Create a new match record and return it"""
    
    rec = None
    folks_id = cleanRecordID(folks_id)
    bike_id = cleanRecordID(bike_id)
    if not match_date:
        match_date = local_datetime_now()
        
    try:
        payment_amt = float(payment_amt)
    except:
        payment_amt = 0.0
        
    if folks_id and bike_id:
        d = {'recipient_id':folks_id,'bike_id':bike_id,'payment_amt':payment_amt,'match_date':match_date}
        match = Match(g.db)
        rec = match.new()
        match.update(rec,d)
        match.save(rec)
        match.commit()
        
    return rec
    
    

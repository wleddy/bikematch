from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString
from shotglass2.takeabeltof.utils import looksLikeEmailAddress, formatted_phone_number
from bikematch.models import MatchLocation
import pdb

PRIMARY_TABLE = MatchLocation

mod = Blueprint('location',__name__, template_folder='templates/location', url_prefix='/location',static_folder='static/')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Location'


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

    # view.list_fields = [
#             {'name':'id','label':'ID','class':'w3-hide-small','search':True},
#             {'name':'start','label':'Date','type':'date','search':'date'},
#         ]
#
#     view.export_fields = None
#
    
    return view.dispatch_request()
    

## Edit the PRIMARY_TABLE
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title.replace("_",' ').title())
    
    # pdb.set_trace()
    
    view = EditView(PRIMARY_TABLE,g.db,rec_id=rec_id)
    # view.edit_fields = [
    #     {'name':'start','label':'Date','type':'datetime','req':True},
    #     {'name':'number_of_slots',},
    #     {'name':'slot_minutes',},
    #     {'name':'location_id','req':True},
    # ]
    view.update() # update record and save
    
    if view.stay_on_form or not view.success:
        return view.render() # re-display the form
    
    return redirect(g.listURL)
    

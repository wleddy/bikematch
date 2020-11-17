from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.takeabeltof.texting import TextMessage, TextResponse
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.takeabeltof.views import TableView, ListFilter
from shotglass2.users.admin import login_required, table_access_required

mod = Blueprint('sms_response',__name__, template_folder='templates/sms_response', url_prefix='/sms')


@mod.route('/<path:path>',methods=['GET','POST',])
@mod.route('/<path:path>/',methods=['GET','POST',])
def handle_request(path=''):
    """Handle sms requests from twilio"""
    resp = TextResponse()
    resp.create_message("Hello World!")
    
    return str(resp)

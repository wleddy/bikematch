from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint, Response
from shotglass2.takeabeltof.texting import TextMessage, TextResponse
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.takeabeltof.views import TableView, ListFilter
from shotglass2.users.admin import login_required, table_access_required

mod = Blueprint('sms_response',__name__, template_folder='templates/sms_response', url_prefix='/sms')


@mod.route('/',methods=['GET','POST',])
def handle_request():
    """Handle sms requests from twilio"""
            
    resp = TextResponse(request)
    # resp now contains these properties:
    #   resp.body = the text sent to us
    #   resp.from_number = the phone number that messaged us
    #   resp.to_number = the phone number we used to message the caller
    # if for some reason, the properties were not set, they will
    # contain the empty string
    
    # At this point, create your message text
    mess = "Hello World!"
    if resp.to_number or resp.from_number:
        mess = "Hello {to_} from {from_}".format(to_=resp.to_number,from_=resp.from_number)
        
    #  and pass it to resp
    resp.create_message(mess)
    # you can test resp.success and resp.result_text to see how it went
    
    # you can now attach media, if you like
    url = url_for('static',filename='images/header-logo.jpg') # a site relative path 
    # or
    # url = "http://{host_name}/{media_path}" # an absolut url
    
    # and attach it to the message
    resp.attach_media(url)
    # as many as you want...
    url = url_for('static',filename='favicon.png') # a site relative path 
    resp.attach_media(url)
    
    #finally, send the response
    return resp.render_response()
    

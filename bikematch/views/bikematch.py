import os
import json
from pathlib import Path
from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response, safe_join
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import render_markdown_for, printException, handle_request_error, send_static_file, \
    cleanRecordID, looksLikeEmailAddress, formatted_phone_number
from shotglass2.takeabeltof.file_upload import FileUpload
from shotglass2.takeabeltof.mailer import Mailer, email_admin
from shotglass2.takeabeltof.date_utils import datetime_as_string, local_datetime_now, date_to_string, getDatetimeFromString
from shotglass2.takeabeltof.views import TableView
from bikematch.models import Match
from werkzeug.exceptions import RequestEntityTooLarge

    
mod = Blueprint('bikematch',__name__, template_folder='templates/bikematch', url_prefix='', static_folder="static/")


def setExits():
    g.homeURL = url_for('bikematch.home')
    # g.listURL = url_for('bikematch.display')
    # g.editURL = url_for('bikematch.edit')
    # g.deleteURL = url_for('bikematch.delete')
    g.contactURL = url_for('bikematch.contact')
    g.title = 'Home'

@mod.route('/')
def home():
    setExits()
    g.title = 'Home'
    g.suppress_page_header = True

    return render_template('index.html',)


@mod.route('/ihaveabike', methods=['POST', 'GET',])
@mod.route('/ihaveabike/', methods=['POST', 'GET',])
def haveabike():
    """handle bike donation contact"""
    setExits()
    g.title = 'I Have a Bike'
    
    return sendcontact(html_template='haveabike_contact.html',
                        subject='I have a Bike',
                        email_template='email/haveabike_email.html',
                        custom_message=render_markdown_for('haveabike_contact.md',mod),
                        )
                        
    
@mod.route('/contact', methods=['POST', 'GET',])
@mod.route('/contact/', methods=['POST', 'GET',])
def contact(**kwargs):
    setExits()
    g.title = 'Contact Us'
    return sendcontact(**kwargs)


def sendcontact(**kwargs):
    """Send an email to the administator or contact specified.
    
    kwargs:
    
        to_addr: the address to send to
        
        to_contact: Name of contact
        
        subject: The email subject text
        
        custom_message: Message to display at top of contact form. should be html
        
        html_template: The template to use for the contact form
    
    """
    from shotglass2.takeabeltof.mailer import send_message
    
    #import pdb;pdb.set_trace()
   
    site_config = get_site_config()
    show_form = True
    context = {}
    success = True
    bcc=None
    passed_quiz = False
    mes = "No errors yet..."
    to = []
    
    if not kwargs and request.form and 'kwargs' in request.form:
        kwargs = json.loads(request.form.get('kwargs','{}'))
        
    subject = kwargs.get('subject',"Contact from {}".format(site_config['SITE_NAME']))
    html_template = kwargs.get('html_template',"contact.html")
    email_template = kwargs.get('email_template',"email/contact_email.html")
    to_addr = kwargs.get('to_addr')
    to_contact = kwargs.get('to_contact',to_addr)
    custom_message = kwargs.get('custom_message')
    if to_addr:
        to.append((to_contact,to_addr))
        
    if custom_message:
        rendered_html = custom_message
    else:
        rendered_html = render_markdown_for('contact.md',mod)
    
    if request.form:
        quiz_answer = request.form.get('quiz_answer',"A")
        if quiz_answer.upper() == "C":
            passed_quiz = True
        else:
            flash("You did not answer the quiz correctly.")
        if request.form['email'] and passed_quiz:
            context.update({'date':datetime_as_string()})
            for key, value in request.form.items():
                context.update({key:value})
                
            # get best contact email
            if not to:
                # See if the contact info is in Prefs
                try:
                    from shotglass2.users.views.pref import get_contact_email
                    contact_to = get_contact_email()
                    if contact_to:
                        to.append(contact_to)
                except Exception as e:
                    printException("Need to update home.contact to find contacts in prefs.","error",e)
                    
                try:
                    if not to:
                        to = [(site_config['CONTACT_NAME'],site_config['CONTACT_EMAIL_ADDR'],),]
                    if site_config['CC_ADMIN_ON_CONTACT'] and site_config['ADMIN_EMAILS']:
                        bcc = site_config['ADMIN_EMAILS']
                    
                except KeyError as e:
                    mes = "Could not get email addresses."
                    mes = printException(mes,"error",e)
                    if to:
                        #we have at least a to address, so continue
                        pass
                    else:
                        success = False
                    
            if success:
                # Ok so far... Try to send
                success, mes = send_message(
                                    to,
                                    subject = subject,
                                    html_template = email_template,
                                    context = context,
                                    reply_to = request.form['email'],
                                    bcc=bcc,
                                    custom_message=custom_message,
                                    kwargs=kwargs,
                                )
        
            show_form = False
        else:
            context = request.form
            flash('You left some stuff out.')
            
    if success:
        return render_template(html_template,
            rendered_html=rendered_html, 
            show_form=show_form, 
            context=context,
            passed_quiz=passed_quiz,
            kwargs=kwargs,
            )
            
    handle_request_error(mes,request,500)
    flash(mes)
    return render_template('500.html'), 500
        
    
@mod.route('/bikematch/<path:filename>', methods=['GET',])
@mod.route('/bikematch/<path:filename>/', methods=['GET',])
def render_for(filename=None):
    """
    The idea is to create a mechanism to serve simple files without
    having to modify the bikematch.home module

    create url as {{ url_for('bikematch.render_for', filename='<name of template>' ) }}

    filename must not have an extension. 

    First see if a file ending in the extension .md or .html
    exists in the /templates/bikematch directroy and serve that if found.

    markdown files will be rendered in the markdown.html template.
    html files will be rendered as a normal freestanding template.
    """

    # templates for this function can only be in the root tempalate/bikematch directory
    temp_path = 'templates/bikematch' 
    path = None

    if filename:
        for extension in ['md','html',]:
            file_loc = os.path.join(os.path.dirname(os.path.abspath(__name__)),temp_path,filename + '.' + extension)
            if os.path.isfile(file_loc):
                path = file_loc
                break
            else:
                pass

    if path:
        setExits()
        g.title = filename.replace('_',' ').title()

        if extension == 'md':
            # use the markdown.html default path
            #rendered_html = render_markdown_for(path)
            return render_template('markdown.html',rendered_html=render_markdown_for(path))
        else:
            # use the standard layout.html template
            return render_template(filename + '.html')

    else:
        return abort(404)


@mod.route('/robots.txt', methods=['GET',])
def robots():
    #from shotglass2.shotglass import get_site_config
    return redirect('/static/robots.txt')

import os
import json
from pathlib import Path
from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response, safe_join
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import render_markdown_for, printException, handle_request_error, send_static_file, \
    cleanRecordID, looksLikeEmailAddress
from shotglass2.takeabeltof.file_upload import FileUpload
from shotglass2.takeabeltof.date_utils import datetime_as_string, local_datetime_now, date_to_string, getDatetimeFromString
from shotglass2.takeabeltof.views import TableView
from bikematch.models import DonorsAndRecipients, Match
from werkzeug.exceptions import RequestEntityTooLarge

    
mod = Blueprint('bikematch',__name__, template_folder='templates/', url_prefix='', static_folder="static/")


def setExits():
    g.homeURL = url_for('bikematch.home')
    g.listURL = url_for('bikematch.display')
    g.editURL = url_for('bikematch.edit')
    g.deleteURL = url_for('bikematch.delete')
    g.contactURL = url_for('bikematch.contact')
    g.title = 'Home'

@mod.route('/')
def home():
    setExits()
    g.title = 'Home'
    g.suppress_page_header = False
    rendered_html = render_markdown_for('index.md',mod)

    return render_template('bikematch/index.html',rendered_html=rendered_html,)



# this handles table list and record delete
@mod.route('/dr/<path:path>',methods=['GET','POST',])
@mod.route('/dr/<path:path>/',methods=['GET','POST',])
@mod.route('/dr/',methods=['GET','POST',])
@table_access_required(DonorsAndRecipients)
def display(path=None):
    # import pdb;pdb.set_trace()
    
    view = TableView(DonorsAndRecipients,g.db)
    # optionally specify the list fields
    view.list_fields = [
            {'name':'id','label':'ID','class':'w3-hide-medium w3-hide-small','search':True},
            {'name':'created','label':'Added','type':'date', 'search':'date'},
            {'name':'full_name',},
            {'name':'d_or_r','label':'Type'},
            {'name':'priority',},
            {'name':'neighborhood','class':'w3-hide-small'},
            {'name':'bike_type','class':'w3-hide-small',},
            {'name':'bike_size','class':'w3-hide-small',},
        ]
    
    return view.dispatch_request()

    
        
@mod.route('/dr/edit/<int:rec_id>', methods=['POST', 'GET',])
@mod.route('/dr/edit/<int:rec_id>/', methods=['POST', 'GET',])
@mod.route('/dr/edit', methods=['POST', 'GET',])
@mod.route('/dr/edit/', methods=['POST', 'GET',])
@table_access_required(DonorsAndRecipients)
def edit(rec_id=None):
    """Edit or create contact records including uploaded images"""

    # import pdb;pdb.set_trace()
    
    setExits()
    g.title = "Edit Donor / Recipient Record"
    site_config = get_site_config()
    save_success = False
    try:
        rec_id = cleanRecordID(request.form.get('id',rec_id))
    except RequestEntityTooLarge as e:
        flash("The image file you submitted was too large. Maximum size is {} MB".format(request.max_content_length))
        return redirect(g.listURL)
        
    if rec_id < 0:
        flash('Invalid Record ID')
        return redirect(g.listURL)
        
            
    contact = DonorsAndRecipients(g.db)
    if rec_id == 0:
        rec = contact.new()
        rec.created = date_to_string(local_datetime_now(),'date')
    else:
        rec = contact.get(rec_id)
        if not rec:
            flash("Record not Found")
            return redirect(g.listURL)
    
    if request.form:
        contact.update(rec,request.form)
        if valididate_form(rec):
            contact.save(rec)
            
            file = request.files.get('image_file')
            if file and file.filename:
                upload = FileUpload(local_path=mod.name)
                filename = file.filename
                if rec.first_name and rec.last_name:
                    # set the filename to the name of the donor
                    #get the extension
                    x = filename.find('.')
                    if x > 0:
                        filename = rec.first_name.lower() + "_" + rec.last_name.lower() + filename[x:].lower()
                        upload.save(file,filename=filename)
                        if upload.success:
                            rec.image_path = upload.saved_file_path_string
                            contact.save(rec,commit=True)
                            save_success = True
                        else:
                            flash(upload.error_text)
                    else:
                        # there must be an extenstion
                        flash('The image file must have an extension at the end of the name.')
                        
            else:
                contact.commit()
                save_success = True
        
    if save_success:
        return redirect(g.listURL)
    else:
        return render_template('bikematch/dr/dr_edit.html',rec=rec,)
    
    
@mod.route('/dr/delete/<int:rec_id>', methods=['POST', 'GET',])
@mod.route('/dr/delete/<int:rec_id>/', methods=['POST', 'GET',])
@mod.route('/dr/delete', methods=['POST', 'GET',])
@mod.route('/dr/delete/', methods=['POST', 'GET',])
@table_access_required(DonorsAndRecipients)
def delete(rec_id=None):
    """View or create donor/recipient records including uploaded images"""

    setExits()
    g.title = "Delete Donor / Recipient Record"
    # import pdb;pdb.set_trace()
    rec_id = cleanRecordID(rec_id)
    dr = DonorsAndRecipients(g.db)
    rec = dr.get(rec_id)
        
    if rec:
        if rec.image_path:
            upload = FileUpload()
            path = upload.get_file_path(rec.image_path)
            if path.exists() and not path.is_dir():
                path.unlink() #remove file
        dr.delete(rec.id,commit=True)
    else:
        flash('Invalid Record ID')
        
    return redirect(g.listURL)
        

@mod.route('/ihaveabike', methods=['POST', 'GET',])
@mod.route('/ihaveabike/', methods=['POST', 'GET',])
def haveabike():
    """handle bike donation contact"""
    setExits()
    g.title = 'I Have a Bike'
    return redirect('http://bikematch.safelanes.org/sacramento/donate/')
    
    return sendcontact(html_template='bikematch/haveabike_contact.html',
                        subject='I have a Bike',
                        email_template='bikematch/email/haveabike_email.html',
                        custom_message=render_markdown_for('bikematch/haveabike_contact.md',mod),
                        )
                        
@mod.route('/ineedabike', methods=['POST', 'GET',])
@mod.route('/ineedabike/', methods=['POST', 'GET',])
def needabike():
    """handle request for a bike"""
    setExits()
    g.title = 'I Need a Bike'
    
    return redirect('http://bikematch.safelanes.org/sacramento/request/')
        
    return sendcontact(html_template='bikematch/needabike_contact.html',
                        subject='Need A Bike',
                        email_template='bikematch/email/needabike_email.html',
                        custom_message=render_markdown_for('bikematch/needabike_contact.md',mod),
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


def valididate_form(rec):
    valid_form = True
    
    if not rec.first_name or not rec.last_name:
        flash("You must enter your full name")
        valid_form = False
    if not rec.email.strip():
        flash("You must enter your email address")
        valid_form = False
    elif not looksLikeEmailAddress(rec.email):
        flash("That is not a valid email address")
        valid_form = False
        
    if not rec.city.strip():
        flash("You must enter your city name")
        valid_form = False
    if not rec.zip.strip():
        flash("You must enter your zip code")
        valid_form = False
    if not rec.neighborhood.strip():
        flash("You must enter your neighborhood")
        valid_form = False
    if not rec.bike_size.strip():
        flash("You must specify your height")
        valid_form = False
    if not rec.bike_type.strip():
        flash("You must specify a bike type")
        valid_form = False
        
    temp_date = getDatetimeFromString(rec.created.strip())
    if not temp_date:
        flash("The 'Created' date is not a valid date")
        valid_form = False
        
        
        
        
    return valid_form
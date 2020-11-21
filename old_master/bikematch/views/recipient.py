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
from bikematch.models import Recipient, Match
from werkzeug.exceptions import RequestEntityTooLarge

    
mod = Blueprint('recipient',__name__, template_folder='templates/recipient', url_prefix='', static_folder="static/")


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Recipients'


# this handles table list and record delete
@mod.route('/recipients/<path:path>',methods=['GET','POST',])
@mod.route('/recipients/<path:path>/',methods=['GET','POST',])
@mod.route('/recipients/',methods=['GET','POST',])
@table_access_required(Recipient)
def display(path=None):
    # import pdb;pdb.set_trace()
    
    view = TableView(Recipient,g.db)
    # optionally specify the list fields
    view.list_fields = [
            {'name':'id','label':'ID','class':'w3-hide-medium w3-hide-small','search':True},
            {'name':'created','label':'Added','type':'date', 'search':'date'},
            {'name':'full_name',},
            {'name':'priority',},
            {'name':'neighborhood','class':'w3-hide-small'},
            {'name':'bike_type','class':'w3-hide-small',},
            {'name':'bike_size','class':'w3-hide-small',},
            {'name':'phone','list':False,},
            {'name':'email','list':False,},
        ]
        
    view.list_search_widget_extras_template = 'dr_list_search_widget_extras.html'

    view.export_fields = [
        {'name':'id'},
        {'name':'first_name'},
        {'name':'last_name'},
        {'name':'phone'},
        {'name':'email'},
        {'name':'neighborhood'},
        {'name':'created', 'type':'date'},
        {'name':'bike_size'},
        {'name':'bike_type'},
        {'name':'priority'},
        {'name':'occupation'},
        {'name':'request_comment'},
    ]

    return view.dispatch_request()

    
        
@mod.route('/recipients/edit/<int:rec_id>', methods=['POST', 'GET',])
@mod.route('/recipients/edit/<int:rec_id>/', methods=['POST', 'GET',])
@mod.route('/recipients/edit', methods=['POST', 'GET',])
@mod.route('/recipients/edit/', methods=['POST', 'GET',])
@table_access_required(Recipient)
def edit(rec_id=None):
    """Edit or create contact records including uploaded images"""

    # import pdb;pdb.set_trace()
    
    setExits()
    g.title = "Edit Recipient Record"
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
        
            
    recipient = Recipient(g.db)
    if rec_id == 0:
        rec = recipient.new()
        rec.created = date_to_string(local_datetime_now(),'date')
    else:
        rec = recipient.get(rec_id)
        if not rec:
            flash("Record not Found")
            return redirect(g.listURL)
    
    if request.form:
        recipient.update(rec,request.form)
        if valididate_form(rec):
            # Format the phone number
            rec.phone = formatted_phone_number(rec.phone)
            recipient.save(rec)
            
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
                            recipient.save(rec,commit=True)
                            save_success = True
                        else:
                            flash(upload.error_text)
                    else:
                        # there must be an extenstion
                        flash('The image file must have an extension at the end of the name.')
                        
            else:
                recipient.commit()
                save_success = True
        
    if save_success:
        return redirect(g.listURL)
    else:
        return render_template('recipient_edit.html',rec=rec,)
    
    
@mod.route('/recipients/delete/<int:rec_id>', methods=['POST', 'GET',])
@mod.route('/recipients/delete/<int:rec_id>/', methods=['POST', 'GET',])
@mod.route('/recipients/delete', methods=['POST', 'GET',])
@mod.route('/recipients/delete/', methods=['POST', 'GET',])
@table_access_required(Recipient)
def delete(rec_id=None):
    """View or create donor/recipient records"""

    setExits()
    g.title = "Delete Recipient Record"
    # import pdb;pdb.set_trace()
    rec_id = cleanRecordID(rec_id)
    dr = Recipient(g.db)
    rec = dr.get(rec_id)
        
    if rec:
        dr.delete(rec.id,commit=True)
    else:
        flash('Invalid Record ID')
        
    return redirect(g.listURL)
        

@mod.route('/ineedabike', methods=['POST', 'GET',])
@mod.route('/ineedabike/', methods=['POST', 'GET',])
def needabike():
    """handle request for a bike"""
    setExits()
    g.title = 'I Need a Bike'
    g.editURL = url_for(".needabike")
    g.cancelURL = url_for('bikematch.home')
    recipient = Recipient(g.db)
    rec = recipient.new()

    # Validate input
    if request.form:
        recipient.update(rec,request.form)
        rec.created = date_to_string(local_datetime_now(),'date')
        rec.phone = formatted_phone_number(rec.phone)
        rec.status = 'Open'
        rec.priority = 'New'
        if valididate_form(rec):
            recipient.save(rec,commit=True)
            rec = recipient.get(rec.id) #get a fresh copy
            site_config = get_site_config()

            # inform sysop of new request
            mailer = Mailer(None,rec=rec)
            mailer.text_template = 'email/request_admin_email.txt'
            mailer.subject = "Bike Request Submitted"
            mailer.send()
            # Inform recipient that request was received
            mailer = Mailer((rec.full_name,rec.email),rec=rec)
            mailer.text_template = 'email/request_recipient_email.txt'
            mailer.subject = "Your Bike Match request has been recieved"
            mailer.bcc = (site_config['MAIL_DEFAULT_SENDER'],site_config['MAIL_DEFAULT_ADDR'])
            mailer.send()
            if not mailer.success:
                mes = "Error: {}".format(mailer.result_text)
                email_admin(subject="Error sending Need a bike email",message=mes)

            return render_template('need_a_bike_success.html')

    # display Recipient form
    return render_template('need_a_bike_form.html',rec=rec)


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
    else:
        rec.created = temp_date




    return valid_form
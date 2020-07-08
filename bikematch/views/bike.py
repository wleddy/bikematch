from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString, date_to_string
from shotglass2.takeabeltof.file_upload import FileUpload
from shotglass2.takeabeltof.utils import looksLikeEmailAddress, formatted_phone_number
from bikematch.models import Bike, Recipient
from werkzeug.exceptions import RequestEntityTooLarge

PRIMARY_TABLE = Bike

mod = Blueprint('bike',__name__, template_folder='templates/bike', url_prefix='/bike',static_folder='static/')


def setExits():
    g.homeURL = url_for('bikematch.home')
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.contactURL = url_for('bikematch.contact')
    
    g.title = 'Bikes'


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
            {'name':'id','label':'ID','class':'w3-hide-medium w3-hide-small','search':True},
            {'name':'created','label':'Added','type':'date', 'search':'date'},
            {'name':'full_name',},
            {'name':'status','class':'w3-hide-small'},
            {'name':'bike_type',},
            {'name':'bike_size',},
            {'name':'phone','list':False,},
            {'name':'email','list':False,},
        ]
    
    view.list_search_widget_extras_template = 'dr_list_search_widget_extras.html'
    
    return view.dispatch_request()
    

## Edit the PRIMARY_TABLE
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    # import pdb;pdb.set_trace()
    
    setExits()
    g.title = "Edit Bike Record"
    site_config = get_site_config()
    save_success = False
        
    try:
        rec_id = cleanRecordID(request.form.get('id',rec_id))
    except RequestEntityTooLarge as e:
        # There does not seem to be a way to do anything with request.form if the content exceeds the limit
        flash("The image file you submitted was too large. Maximum size is {} MB".format(request.max_content_length/2048))
        return redirect(g.listURL)
        
    if rec_id < 0:
        flash('Invalid Record ID')
        return redirect(g.listURL)
        
            
    contact = Bike(g.db)
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
            # Format the phone number
            rec.phone = formatted_phone_number(rec.phone)
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
        return render_template('bike_edit.html',rec=rec,)
    
    
@mod.route('/delete/<int:rec_id>', methods=['POST', 'GET',])
@mod.route('/delete/<int:rec_id>/', methods=['POST', 'GET',])
@mod.route('/delete', methods=['POST', 'GET',])
@mod.route('/delete/', methods=['POST', 'GET',])
@table_access_required(PRIMARY_TABLE)
def delete(rec_id=None):
    """View or create donor/recipient records including uploaded images"""

    setExits()
    g.title = "Delete Bike Record"
    # import pdb;pdb.set_trace()
    rec_id = cleanRecordID(rec_id)
    bike = PRIMARY_TABLE(g.db)
    rec = bike.get(rec_id)
        
    if rec:
        if rec.match_id is not None:
            flash("That Bike is already Matched. You must delete the match first.")
            return redirect(g.listURL)
                
        if rec.image_path:
            upload = FileUpload()
            path = upload.get_file_path(rec.image_path)
            if path.exists() and not path.is_dir():
                path.unlink() #remove file
        bike.delete(rec.id,commit=True)
    else:
        flash('Invalid Record ID')
        
    return redirect(g.listURL)    
    
    
@mod.route('view/<int:rec_id>', methods=['GET',])
@mod.route('view/<int:rec_id>/', methods=['GET',])
@mod.route('view', methods=['GET',])
@mod.route('view/', methods=['GET',])
def view_bike(rec_id=None):
    """Display the information about a bike"""

    setExits()
    g.title = "View Bike"

    rec_id = cleanRecordID(rec_id)

    if rec_id > 0:
        rec = Bike(g.db).get(rec_id)
        if rec:
            return render_template('view_bike.html',rec=rec)

    flash("That does not look like a valid bike record...")
    return redirect(g.homeURL)


@mod.route('question/<int:rec_id>', methods=['GET',])
@mod.route('question/<int:rec_id>/', methods=['GET',])
@mod.route('question', methods=['GET',])
@mod.route('question/', methods=['GET',])
def question(rec_id=None):
    """Viewer has a question about a bike"""

    setExits()
    g.title = "Bike Question"

    rec_id = cleanRecordID(rec_id)

    if rec_id > 0:
        rec = Bike(g.db).get(rec_id)
        if rec:
            rendered_html = "<p>Please type your message below the info section in the &quot;Comment&quot; section</p>"
            bike_info = """
+++++++++ please leave this section as-is ++++++++++++
A question regarding Bike ID = {}
Size: {}
Type: {}
+++++++++ please leave this section as-is ++++++++++++

""".format(rec.id,rec.bike_size,rec.bike_type)
            context = {'comment':bike_info}
            return render_template('bike_question.html',rec=rec,rendered_html=rendered_html,context=context,show_form=True)

    flash("That does not look like a valid bike record...")
    return redirect(g.homeURL)


@mod.route('/ihaveabike', methods=['POST', 'GET',])
@mod.route('/ihaveabike/', methods=['POST', 'GET',])
def haveabike():
    """handle bike donation contact"""
    setExits()
    g.title = 'I Have a Bike'
    # return redirect('http://bikematch.safelanes.org/sacramento/donate/')

    return sendcontact(html_template='haveabike_contact.html',
                        subject='I have a Bike',
                        email_template='email/haveabike_email.html',
                        custom_message=render_markdown_for('haveabike_contact.md',mod),
                        )



def valididate_form(rec):
    # Validate the form
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
    

from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString, date_to_string
from shotglass2.takeabeltof.file_upload import FileUpload
from shotglass2.takeabeltof.jinja_filters import two_decimal_string as money
from shotglass2.takeabeltof.utils import looksLikeEmailAddress, formatted_phone_number
from bikematch.models import Bike, BikeImage
from werkzeug.exceptions import RequestEntityTooLarge

PRIMARY_TABLE = Bike
STATUS_SELECT_OBJ_ID = 'status_select_obj' #Bike Status select object id
BIKE_IMAGE_PATH = 'bikematch/bikes/'
    
mod = Blueprint('bike',__name__, template_folder='templates/bike', url_prefix='/bike',static_folder='static/')


def setExits():
    g.homeURL = url_for('bikematch.home')
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.contactURL = url_for('bikematch.contact')
    
    g.title = 'Bikes'


from shotglass2.takeabeltof.views import TableView

class BikeView(TableView):
    def __init__(self,table,db,**kwargs):
        super().__init__(table,db,**kwargs)
    
        self.STATUS_SELECT_OBJ_ID = STATUS_SELECT_OBJ_ID
        self.list_search_widget_extras_template = 'bike_list_search_widget_extras.html'
        self.allow_record_addition = False
        
    def select_recs(self,**kwargs):
        """Make a selection of recs based on the current filters"""
        # look in session for the saved search...
        filters = self.get_list_filters()
        
        status_filter = session.get(STATUS_SELECT_OBJ_ID,'all').lower()
        if status_filter != 'all':
            filters.where += ' and lower(bike_status) = "{}"'.format(status_filter)
            
        self.recs = self.table.select(where=filters.where,order_by=filters.order_by,**kwargs)
        
 
# this handles table list and record delete
@mod.route('/<path:path>',methods=['GET','POST',])
@mod.route('/<path:path>/',methods=['GET','POST',])
@mod.route('/',methods=['GET','POST',])
@table_access_required(PRIMARY_TABLE)
def display(path=None):
    # import pdb;pdb.set_trace()
    
    view = BikeView(PRIMARY_TABLE,g.db)

    view.list_fields = [
            {'name':'id','label':'ID','class':'w3-hide-medium w3-hide-small','search':True},
            {'name':'created','label':'Added','type':'date', 'search':'date'},
            {'name':'bike_comment','label':'Description'},
            {'name':'pedal_length',},
            {'name':'bike_status',"label":'Status'},
            {'name':'staff_comment','list':False},
        ]
    
    view.export_fields = view.list_fields
    
    return view.dispatch_request()

    
@mod.route('/set_list_status', methods=['POST'])
@mod.route('/set_list_status/', methods=['POST'])
def set_list_status():
    """Record the selected bike status for the bike list page"""

    session[STATUS_SELECT_OBJ_ID] = request.form.get(STATUS_SELECT_OBJ_ID,"all")
    
    return "OK"


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
        
            
    bike = Bike(g.db)
    if rec_id == 0:
        rec = bike.new()
        rec.created = date_to_string(local_datetime_now(),'date')
    else:
        rec = bike.get(rec_id)
        if not rec:
            flash("Record not Found")
            return redirect(g.listURL)
        ## convert estimated_value field to a string in the money format
        if rec.estimated_value:
            rec.estimated_value = money(rec.estimated_value)
            
    if request.form:
        # import pdb;pdb.set_trace()
        
        bike.update(rec,request.form)
        if valididate_form(rec):
            bike.save(rec)
            
            file = request.files.get('image_file')
            if file and file.filename:
                upload = FileUpload(local_path='{}{}'.format(BIKE_IMAGE_PATH,rec.id))
                filename = file.filename
                x = filename.find('.')
                if x > 0:
                    upload.save(file,filename=filename)
                    if upload.success:
                        images = BikeImage(g.db)
                        image_rec = images.new()
                        image_rec.image_path = upload.saved_file_path_string
                        image_rec.bike_id = rec.id
                        images.save(image_rec,commit=True)
                        save_success = True
                    else:
                        flash(upload.error_text)
                else:
                    # there must be an extenstion
                    flash('The image file must have an extension at the end of the name.')
                        
            else:
                bike.commit()
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
        if rec.reservation_id is not None:
            flash("That Bike is currently Reserved. You must resolve the reservation first.")
            return redirect(g.listURL)
                
        if rec.image_path:
            upload = FileUpload()
            path = upload.get_file_path(rec.image_path)
            if path.exists() and not path.is_dir():
                path.unlink() #remove file
            # Delete the enclosing directory if empty
            path = path.parent
            try:
                path.rmdir()
            except:
                # not emtpy, most likely
                pass
                
        bike.delete(rec.id,commit=True)
        # bike_image records are deleted by cascade
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

    if not validate_pedal_length(rec.min_pedal_length):
        flash("You must specify the minimum pedal_length")
        valid_form = False

    if not validate_pedal_length(rec.max_pedal_length):
        flash("You must specify the maximum pedal_length")
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
    
    try:
        if not rec.estimated_value:
            rec.estimated_value = 0
        temp = float(rec.estimated_value)
        rec.estimated_value = temp
    except:
        flash("The estimated_value must be a number")
        valid_form = False
        
    return valid_form
    
def validate_pedal_length(pedal_len):
    # see if the pedal length is a number
    if isinstance(pedal_len,(int,float)):
        return True
    try:
        pedal_len = float(pedal_len.strip())
        if pedal_len:
            return True
    except:
        pass
        
    return False
        
from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response, safe_join
from bikematch.models import Reservation, Bike, Folks, Match
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString
from shotglass2.takeabeltof.utils import looksLikeEmailAddress, formatted_phone_number

PRIMARY_TABLE = Reservation
    
mod = Blueprint('reservation',__name__, template_folder='templates/reservation', url_prefix='/reservation', static_folder="static/")


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Reservation'


from shotglass2.takeabeltof.views import TableView

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
    #         {'name':'id','label':'ID','class':'w3-hide-small','search':True},
    #         {'name':'full_name','label':'Name'},
    #         {'name':'email',},
    #         {'name':'phone',},
    #     ]
    #
    # view.export_fields = None
    #

    return view.dispatch_request()
    

@mod.route('/reservation/reserve', methods=['GET', 'POST'])
@mod.route('/reservation/reserve/', methods=['GET', 'POST'])
def reserve():
    return "Not done"
    
    
@mod.route('/reservation/edit', methods=['POST', 'GET'])
@mod.route('/reservation/edit/', methods=['POST', 'GET'])
@mod.route('/reservation/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)

    reservation = PRIMARY_TABLE(g.db)
    rec = None

    if rec_id == None:
        rec_id = request.form.get('id',request.args.get('id',-1))

    rec_id = cleanRecordID(rec_id)
    #import pdb;pdb.set_trace

    if rec_id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)

    if not request.form:
        """ if no form object, send the form page """
        if rec_id == 0:
            rec = reservation.new()
            rec.reservation_date = local_datetime_now()
        else:
            rec = reservation.get(rec_id)
            if not rec:
                flash("Unable to locate that record")
                return redirect(g.listURL)
    else:
        #have the request form
        # import pdb;pdb.set_trace()
        if rec_id:
            rec = reservation.get(rec_id)
        else:
            # its a new unsaved record
            rec = reservation.new()
            
        reservation.update(rec,request.form)

        if valididate_form(rec):
            #update the record
            #import pdb;pdb.set_trace()
    
            reservation.update(rec,request.form)
        
            try:
                reservation.save(rec)
                g.db.commit()
            except Exception as e:
                g.db.rollback()
                flash(printException('Error attempting to save '+g.title+' record.',"error",e))

            return redirect(g.listURL)

        else:
            # form did not validate
            pass

    # display form
    return render_template('reservation_edit.html', rec=rec)


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

    return valid_form
    

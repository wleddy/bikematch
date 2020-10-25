from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response, safe_join
from bikematch.models import Reservation, Bike, Folks, Match, MatchDay, Location
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString, date_to_string
from shotglass2.takeabeltof.utils import looksLikeEmailAddress, formatted_phone_number
from datetime import timedelta

PRIMARY_TABLE = Reservation
    
mod = Blueprint('reservation',__name__, template_folder='templates/reservation', url_prefix='/reservation', static_folder="static")


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

    view.list_fields = [
            {'name':'id','label':'ID','class':'w3-hide-small','search':True},
            {'name':'full_name','label':'Name'},
            {'name':'reservation_date','type':'datetime','search':'date'},
            {'name':'email','class':'w3-hide-small',},
            {'name':'phone','class':'w3-hide-small','type':'phone'},
        ]

    view.export_fields = None
    view.allow_record_addition = False


    return view.dispatch_request()
    

@mod.route('/reserve', methods=['POST', 'GET'])
@mod.route('/reserve/', methods=['POST', 'GET'])
def reserve():
    """Visitor wants to reserve a bike for pickup"""
    
    g.title = "Reserve a Bike"
    return_target = url_for("bike.gallery")
    rec = None
    bike = None
    match_day = None
    reservation = Reservation(g.db)
    
    # import pdb;pdb.set_trace()
        
    #Get the next handoff date
    # Reservations close at 6 on the day before the next handoff
    match_day = MatchDay(g.db).select_future()
    if not match_day:
        flash("Sorry, We have no BikeMatch events scheduled at this time.")
        return redirect(return_target)
    else:
        #limit to only the next event
        match_day = match_day[0]
        # get the location for this day
        location = Location(g.db).get(match_day.location_id)
            
        # construct the list of time slots
        time_slots = []
        # find times already reserved
        res_for_day = reservation.query("select reservation_date from reservation where match_day_id = {}".format(match_day.id))
        if res_for_day:
            filled_slots = [getDatetimeFromString(x.reservation_date) for x in res_for_day]
        else:
            filled_slots = []
            
        start = getDatetimeFromString(match_day.start) - timedelta(minutes=match_day.slot_minutes)
        has_open_slot = False
        for t in range(match_day.number_of_slots):
            start = start + timedelta(minutes=match_day.slot_minutes)
            d = {'slot_date':date_to_string(start,'iso_date_tz'),"open":True}
            # is this slot taken?
            if start in filled_slots:
                d['open']=False
            else:
                has_open_slot = True
        
            time_slots.append(d)
        
    if not has_open_slot:
        flash("Sorry, there are no open times available for the next event")
        return redirect(return_target)
    
    if not request.form:
        # All access is by POST (GET is there to stop it going to "display".
        return redirect(return_target)
    else:
        bike = Bike(g.db).get(cleanRecordID(request.form.get('bike_id')))
        if not bike:
            flash("Invalid bike id submitted")
            return redirect(return_target)

        if request.form.get("email"):
            #test if there is already a reservation for this person
            temp_rec = reservation.select(where="lower(email) = '{}'".format(request.form["email"].strip().lower()))
            # if temp_rec:
            #     flash("You already have a bike reserved.")
            #     return redirect(return_target)
                
            if not looksLikeEmailAddress(request.form.get("email")):
                flash("That does not look like a valid email address.")
            else:
                rec = reservation.new()
                reservation.update(rec,request.form)
                if 'first_name' in request.form:
                    if valid_form(rec):
                        reservation.save(rec)
                        reservation.commit()
                        flash("You reservation has been saved. Check for an email confirmation")
                        # Send email confirmation
                        # Send a text confirmation too!
                        return redirect(url_for('bikematch.home'))
    
    # Display the reservation form
    return render_template("reservation_form.html",
        rec=rec,
        bike=bike,
        match_day=match_day,
        time_slots=time_slots,
        location=location,
        )
    
    
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)

    reservation = PRIMARY_TABLE(g.db)
    rec = None
    bike = None
    
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

        if valid_form(rec):
            #update the record
            #import pdb;pdb.set_trace()
    
            reservation.update(rec,request.form)
            # ensure the reservation_date is in iso format
            if "reservation_date" in request.form:
                rec.reservation_date = getDatetimeFromString(request.form["reservation_date"])
        
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
    bike = Bike(g.db).get(rec.bike_id)
    return render_template('reservation_edit.html', 
        rec=rec,
        bike=bike,
        )


def valid_form(rec):
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
        
    if "reservation_date" in request.form and not rec.reservation_date:
        flash("You must pick a reservation time")
        valid_form = False

    return valid_form
    

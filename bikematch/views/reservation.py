from flask import request, session, g, redirect, url_for, abort, \
     render_template, render_template_string, flash, Blueprint, Response, safe_join
from bikematch.models import Reservation, Bike, Folks, Match, MatchDay, Location
from shotglass2.shotglass import get_site_config
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString, date_to_string
from shotglass2.takeabeltof.mailer import Mailer, email_admin
from texting.twilio import TextMessage
from shotglass2.takeabeltof.utils import looksLikeEmailAddress, formatted_phone_number, printException, cleanRecordID, validate_phone_number
from shotglass2.takeabeltof.views import TableView, EditView

from datetime import timedelta

PRIMARY_TABLE = Reservation
    
mod = Blueprint('reservation',__name__, template_folder='templates/reservation', url_prefix='/reservation', static_folder="static")


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Reservation'



class ReservationEdit(EditView):
    """Record and or process a bike reservation"""
        
    def after_get_hook(self):
        """ do anything you want here"""
        self.set_bike()
        
        
    def set_bike(self):
        self.bike = None
        if self.rec:
            self.bike = Bike(self.db).get(cleanRecordID(self.rec.bike_id))
            
                        
    def before_commit_hook(self):
        # if match or un-match this reservation then make the match and redisplay the form
        from bikematch.views import match, folks
        if self.success and (request.form.get('match_this_bike') or request.form.get('un_match_this_bike')):
            # import pdb;pdb.set_trace()
            if request.form.get('match_this_bike'):
                if "payment" in request.form:
                    try:
                        if self.rec.price and float(request.form.get('payment')) < float(self.rec.price):
                            raise ValueError
                    except:
                        self.result_text = "The minimum donation amount for this bike is ${}".format(self.rec.price)
                        self.success = False
                        flash(self.result_text)
                        return

                # add or get a folks record for this recipient
                folks_rec = folks.get_or_create(self.rec)
                if folks_rec:
                    match_rec = match.match_bike(folks_rec.id,self.rec.bike_id,self.rec.payment)
                    if match_rec:
                        self.rec.match_id = match_rec.id
                    else:
                        self.result_text = "Unable to Match record for {}".format(self.rec.email)
                        self.success = False

                else:
                    self.result_text = "Unable to find or create a 'Folks' record for {}".format(self.rec.email)
                    self.success = False

            if request.form.get('un_match_this_bike'):
                # delete a match record
                self.stay_on_form = True #redisplay the form page
                if self.rec.match_id:
                    Match(self.db).delete(self.rec.match_id,commit=True)
                    self.rec.match_id = None
                     
    def validate_form(self):
        valid_form = True
        
        if not self.rec:
            return True

        if not self.rec.email or not self.rec.email.strip():
            flash("You must enter your email address")
            valid_form = False
        elif not looksLikeEmailAddress(self.rec.email):
            flash("That is not a valid email address")
            valid_form = False
        
        if not self.rec.first_name or not self.rec.last_name:
            flash("You must enter your full name")
            valid_form = False
    
        if  self.rec.phone and not validate_phone_number(self.rec.phone):
            flash("That does not look like a valid phone number")
            valid_form = False
            
        if 'reservation_comment' in request.form:
            if not self.rec.reservation_comment or not self.rec.reservation_comment.strip():
                flash("You must tell us why you would like this bike.")
                valid_form = False
                                
        if not self.rec.reservation_date:
            flash("You must pick a reservation time")
            valid_form = False

        return valid_form
        
        

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
            {'name':'bike_id','class':'w3-hide-small',},
            {'name':'bike_status','label':'Status',},
        ]

    view.export_fields = None
    # view.allow_record_addition = False


    return view.dispatch_request()
    

@mod.route('/reserve', methods=['POST', 'GET'])
@mod.route('/reserve/', methods=['POST', 'GET'])
def reserve():
    """Visitor wants to reserve a bike for pickup"""
    setExits()
    g.title = "Reserve a Bike"
    return_target = url_for("bike.gallery")
    
    # import pdb;pdb.set_trace()
        
    res = ReservationEdit(PRIMARY_TABLE,g.db)
    
    # use the end user reservation form form
    res.form_template = "reservation_form.html"
    res.validate_me = 1
    
    # Add the extra properties for the res context
    res.bike = Bike(g.db).get(cleanRecordID(request.form.get('bike_id')))
    if not res.bike or not set_extra_context(res):
        return redirect(return_target)
    
    if request.form.get('validate_me'):
        res.update() # update record and save
        if not res.success:
            return res.render() # re-display the form
    else:
        return res.render() #this is the first time sending the form
        
    res.get() # need to get a fresh select so the values from the related tables are updated
    send_confirmation(res)
    flash("You reservation has been saved. Check for an email confirmation")
    return redirect(url_for('bikematch.home'))
    
def set_extra_context(res):
    #Get the next handoff date
    # Reservations close at 6 on the day before the next handoff
    match_day = MatchDay(g.db).select_future()
    if not match_day:
        flash("Sorry, We have no BikeMatch events scheduled at this time.")
        return False
    else:
        #limit to only the next event
        match_day = match_day[0]
        # get the location for this day
        location = Location(g.db).get(match_day.location_id)
            
        # construct the list of time slots
        time_slots = []
        # find times already reserved
        res_for_day = Reservation(g.db).query("select reservation_date from reservation where match_day_id = {} order by reservation_date".format(match_day.id))
        if res_for_day:
            filled_slots = [getDatetimeFromString(x.reservation_date) for x in res_for_day]
        else:
            filled_slots = []
            
        start = getDatetimeFromString(match_day.start) - timedelta(minutes=match_day.slot_minutes)
        has_open_slot = False
        empty_slots = 0
        for t in range(match_day.number_of_slots):
            start = start + timedelta(minutes=match_day.slot_minutes)
            d = {'slot_date':date_to_string(start,'iso_date_tz'),"open":True}
            # is this slot taken?
            if start in filled_slots:
                d['open']=False
            else:
                empty_slots += 1
                has_open_slot = True
                
            if empty_slots < 4:
                # avoid appointments stretched out too far
                time_slots.append(d)
            else:
                break
        
    if not has_open_slot:
        flash("Sorry, there are no open times available for the next event")
        return False
        
    res.location = location
    res.match_day=match_day
    res.time_slots=time_slots
    return True
        
    
@mod.route('/swap_bike', methods=['POST'])
@mod.route('/swap_bike/', methods=['POST'])
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)
    
    # import pdb;pdb.set_trace()
    res = ReservationEdit(PRIMARY_TABLE,g.db,rec_id)
    res.form_template = "reservation_edit.html"
    
    # if res.rec and not res.rec.id:
    if "swap_bike" in request.path:
        # just changing the bike
        res.stay_on_form = True
        res.update()
        res.get() # need to get a fresh select so the values from the related tables are updated
    else:
        res.update() # update record and save
        
    if res.stay_on_form or not res.success:
        return res.render() # re-display the form
        
    return redirect(g.listURL)
    
    
@mod.route('/email_check', methods=['POST'])
@mod.route('/email_check/', methods=['POST'])
def email_check():
    """Called by javascript to test if this email address is currently being used to reserve a bike"""
    if request.form:
        email_address = request.form.get("email_address",'')
        rec = PRIMARY_TABLE(g.db).select_one(where="lower(email) == '{}'".format(email_address.strip().lower()))
        if rec:
            return "duplicate"
        
    return "ok"
    
    
@mod.route('/cancel_via_email', methods=['get'])
@mod.route('/cancel_via_email/', methods=['get'])
@mod.route('/cancel_via_email/<int:rec_id>', methods=['get'])
@mod.route('/cancel_via_email/<int:rec_id>/', methods=['get'])
def cancel_via_email(rec_id=None):
    """User wants to cancel reservation"""
    setExits()
    g.title = "Reservation Cancelled"
    if rec_id:
        email_admin("BikeMatch Cancelation","User has requested cancellation via email of reservation id: {}".format(rec_id))
        
    return render_template('reservation_cancellation.html')

def send_confirmation(data):
    """Send an email and possibly a text to user to confirm and provide 
    additional details about their appointment
    """

    if data.rec:
        if data.rec.email:
            #send an email
            message = Mailer(
                [("{} {}".format(data.rec.first_name,data.rec.last_name),data.rec.email)],
                subject = 'BikeMatch Confirmation',
                body_is_html = True,
                html_template = 'email/reservation_confirmation.html',
                data=data,
                )
            message.send()
        
        # import pdb;pdb.set_trace()
            
        if data.rec.phone:
            #send a text
            mes = render_template("text/reservation_confirmation.txt",data=data)
            text = TextMessage(data.rec.phone,mes)
            text.send()
            if not text.success:
                email_admin('Texting Error Occurred',text.result_text)

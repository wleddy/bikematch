from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response, safe_join
from bikematch.models import Reservation, Bike, Folks, Match, MatchDay, Location
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString, date_to_string
from shotglass2.takeabeltof.utils import looksLikeEmailAddress, formatted_phone_number
from shotglass2.users.admin import login_required, table_access_required

from datetime import timedelta

PRIMARY_TABLE = Reservation
    
mod = Blueprint('reservation',__name__, template_folder='templates/reservation', url_prefix='/reservation', static_folder="static")


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Reservation'


from shotglass2.takeabeltof.views import TableView

class ReservationEdit():
    """Record and or process a bike reservation"""
    
    def __init__(self,primary_table,db,rec_id=None):
        self.db = db
        self.primary_table = primary_table(self.db)
        self.success = True
        self.result_text = ''
        self.stay_on_form = False
        self.form_template = None
        self.rec_id = rec_id
        self._validate_rec_id() # self.rec_id may have a value now
        self.get() # could be an empty (new) record, existing record or None
        
        
    def get(self):
        # Select an existing record or make a new one
        if not self.rec_id:
            self.rec = self.primary_table.new()
        else:
            self.rec = self.primary_table.get(self.rec_id)
        if not self.rec:
            self.result_text = "Unable to locate that record"
            flash(self.result_text)
            self.success = False
                    
        self.set_bike()
        
    def set_bike(self):
        self.bike = None
        if self.rec:
            self.bike = Bike(self.db).get(cleanRecordID(self.rec.bike_id))
            
            
    def update(self,save_after_update=True):
        # import pdb;pdb.set_trace()
        if request.form:
            self.primary_table.update(self.rec,request.form)
            self.set_bike()
            if self._validate_form():
                if save_after_update:
                    self.save()
            else:
                self.success = False
                self.result_text = "Form Validation Failed"
        else:
            self.success = False
            self.result_text = "No input form provided"
        
        
    def save(self):
        # ensure the reservation_date is in iso format
        if "reservation_date" in request.form:
            self.rec.reservation_date = getDatetimeFromString(request.form["reservation_date"])

        try:
            self.primary_table.save(self.rec)
            self.rec_id = self.rec.id
            
        except Exception as e:
            self.db.rollback()
            self.result_text = printException('Error attempting to save {} record.'.format(self.primary_table.display_name),"error",e)
            flash(self.result_text)
            self.success = False
            return
            
        # if match or un-match this reservation then make the match and redisplay the form
        from bikematch.views import match, folks
        if self.success and (request.form.get('match_this_bike') or request.form.get('un_match_this_bike')):
            # import pdb;pdb.set_trace()
            if request.form.get('match_this_bike'):
                if "donation_amount" in request.form:
                    try:
                        if self.rec.minimum_donation and float(request.form.get('donation_amount')) < float(self.rec.minimum_donation):
                            raise ValueError
                    except:
                        self.result_text = "The minimum donation amount for this bike is ${}".format(self.rec.minimum_donation)
                        self.success = False
                        flash(self.result_text)
                        return
                
                # add or get a folks record for this recipient
                folks_rec = folks.get_or_create(self.rec)
                if folks_rec:
                    match_rec = match.match_bike(folks_rec.id,self.rec.bike_id,self.rec.donation_amount)
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
                    
        self.primary_table.commit()

        
    def render(self):
        if not self.form_template:
            self.form_template = 'reservation_edit.html'
            
        return render_template(self.form_template, 
            data = self,
            bike = self.bike,
            )
        
    def _validate_form(self):
        valid_form = True


        if not self.rec.email or not self.rec.email.strip():
            flash("You must enter your email address")
            valid_form = False
        elif not looksLikeEmailAddress(self.rec.email):
            flash("That is not a valid email address")
            valid_form = False
        
        if not self.rec.first_name or not self.rec.last_name:
            flash("You must enter your full name")
            valid_form = False
    
        if not self.rec.reservation_date:
            flash("You must pick a reservation time")
            valid_form = False
                                
        return valid_form
        
        
    def _validate_rec_id(self):
        if not self.rec_id:
            self.rec_id = request.form.get('id',request.args.get('id',0))

        self.rec_id = cleanRecordID(self.rec_id)

        if self.rec_id < 0:
            self.result_text = "That is not a valid ID"
            self.success = False
            raise ValueError(self.result_text)


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
        res_for_day = Reservation(g.db).query("select reservation_date from reservation where match_day_id = {}".format(match_day.id))
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
    
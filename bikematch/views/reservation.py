from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response, safe_join

mod = Blueprint('reservation',__name__, template_folder='templates/reservation', url_prefix='', static_folder="static/")

def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Reservation'


@mod.route('/ineedabike', methods=['POST', 'GET',])
@mod.route('/ineedabike/', methods=['POST', 'GET',])
def needabike():
    """handle Reervation creation
    Display a searchable photo gallery of bikes
    """
    return "ineeedabike Not implemented yet"
    # setExits()
    # g.title = 'I Need a Bike'
    # g.editURL = url_for(".needabike")
    # g.cancelURL = url_for('bikematch.home')
    # recipient = Recipient(g.db)
    # rec = recipient.new()
    #
    # # Validate input
    # if request.form:
    #     recipient.update(rec,request.form)
    #     rec.created = date_to_string(local_datetime_now(),'date')
    #     rec.phone = formatted_phone_number(rec.phone)
    #     rec.status = 'Open'
    #     rec.priority = 'New'
    #     if valididate_form(rec):
    #         recipient.save(rec,commit=True)
    #         rec = recipient.get(rec.id) #get a fresh copy
    #         site_config = get_site_config()
    #
    #         # inform sysop of new request
    #         mailer = Mailer(None,rec=rec)
    #         mailer.text_template = 'email/request_admin_email.txt'
    #         mailer.subject = "Bike Request Submitted"
    #         mailer.send()
    #         # Inform recipient that request was received
    #         mailer = Mailer((rec.full_name,rec.email),rec=rec)
    #         mailer.text_template = 'email/request_recipient_email.txt'
    #         mailer.subject = "Your Bike Match request has been recieved"
    #         mailer.bcc = (site_config['MAIL_DEFAULT_SENDER'],site_config['MAIL_DEFAULT_ADDR'])
    #         mailer.send()
    #         if not mailer.success:
    #             mes = "Error: {}".format(mailer.result_text)
    #             email_admin(subject="Error sending Need a bike email",message=mes)
    #
    #         return render_template('need_a_bike_success.html')
    #
    # # display Recipient form
    # return render_template('need_a_bike_form.html',rec=rec)


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
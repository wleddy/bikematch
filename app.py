""" Create Flask app

Setup and initialize the flask app

Starts the development server when run from the command line

Args: None

Returns:  None

Raises: None
"""

from flask import Flask, g, session, request, redirect, flash, abort, url_for, session
from flask_mail import Mail
import os
from shotglass2 import shotglass
from shotglass2.takeabeltof.database import Database
from shotglass2.takeabeltof.jinja_filters import register_jinja_filters
from shotglass2.users.admin import Admin
from bikematch.models import Recipient, Match, Bike

# Create app
# # setting static_folder to None allows me to handle loading myself
# app = Flask(__name__, instance_relative_config=True,
#         static_folder=None)
# app.config.from_pyfile('site_settings.py', silent=True)
import logging 
try:
    app = shotglass.create_app(
            __name__,
            instance_path='../data_store/instance',
            config_filename='site_settings.py',
            static_folder=None,
            )
except:
    logging.exception('')


@app.before_first_request
def start_app():
    shotglass.start_logging(app)
    get_db() # ensure that the database file exists
    # shotglass.start_backup_thread(os.path.join(app.root_path,app.config['DATABASE_PATH']))
    # use os.path.normpath to resolve true path to data file when using '../' shorthand
    shotglass.start_backup_thread(os.path.normpath(os.path.join(app.root_path,shotglass.get_site_config()['DATABASE_PATH'])))

@app.context_processor
def inject_site_config():
    # Add 'site_config' dict to template context
    return {'site_config':shotglass.get_site_config()}

# # work around some web servers that mess up root path
# from werkzeug.contrib.fixers import CGIRootFix
# if app.config['CGI_ROOT_FIX_APPLY'] == True:
#     fixPath = app.config.get("CGI_ROOT_FIX_PATH","/")
#     app.wsgi_app = CGIRootFix(app.wsgi_app, app_root=fixPath)

register_jinja_filters(app)


mail = Mail(app)

def init_db(db=None):
    # to support old code
    initalize_all_tables(db)

def initalize_all_tables(db=None):
    """Place code here as needed to initialze all the tables for this site"""
    if not db:
        db = get_db()
        
    shotglass.initalize_user_tables(db)
    
    ### setup any other tables you need here....
    Recipient(db).init_table()
    Match(db).init_table()
    Bike(db).init_table()
    
def get_db(filespec=None):
    """Return a connection to the database.

    If the db path does not exist, create it and initialize the db"""

    if not filespec:
        filespec = shotglass.get_site_config()['DATABASE_PATH']
    
    # This is probobly a good place to change the
    # filespec if you want to use a different database
    # for the current request.

    # test the path, if not found, try to create it
    if shotglass.make_db_path(filespec):
        g.db = Database(filespec).connect()
        initalize_all_tables(g.db)
        
        return g.db
    else:
        # was unable to create a path to the database
        raise IOError("Unable to create path to () in app.get_db".format(filespec))

    
    
@app.context_processor
def inject_site_config():
    # Add 'site_config' dict to template context
    return {'site_config':shotglass.get_site_config()}


@app.before_request
def _before():
    # Force all connections to be secure
    if app.config['REQUIRE_SSL'] and not request.is_secure :
        return redirect(request.url.replace("http://", "https://"))

    #ensure that nothing is served from the instance directory
    if 'instance' in request.url:
        return abort(404)
        
    #import pdb;pdb.set_trace()

    session.permanent = True
    
    shotglass.get_site_config(app)
    shotglass.set_template_dirs(app)
    
    get_db()
    
    # Is the user signed in?
    g.user = None
    if 'user' in session:
        g.user = session['user']
        
    # g.menu_items should be a list of dicts
    #  with keys of 'title' & 'url' used to construct
    #  the items in the main menu
    # g.menu_items = shotglass.get_menu_items()
    # g.menu_items = [{'title':'Home','url':url_for('bikematch.home')},
 #        {'title':'I Need a Bike','url':url_for('recipient.needabike')},
 #        {'title':'I Have a Bike','url':url_for('bikematch.haveabike')},
 #        {'title':'Alternative Sources','url':url_for('bikematch.alternatives')},
 #        ]
    g.menu_items = [
        {'title':'Home','url':None,'drop_down_menu':[
            {'title':'Bikematch Home','url':url_for('bikematch.home')},
            {'title':'SABA Home','url':"http://sacbike.org"},
            ]},        
        ]
    # g.admin items are added to the navigation menu by default
    g.admin = Admin(g.db) # This is where user access rules are stored
    g.admin.register(Recipient,None,display_name='BikeMatch Admin',header_row=True,minimum_rank_required=100)
    g.admin.register(Recipient,url_for('recipient.display'),display_name='Recipients',minimum_rank_required=100)
    g.admin.register(Bike,url_for('bike.display'),display_name='Bikes',minimum_rank_required=100)
    g.admin.register(Match,url_for('match.display'),display_name='Matches',minimum_rank_required=100)
    
    shotglass.user_setup() # g.admin now holds access rules Users, Prefs and Roles

@app.teardown_request
def _teardown(exception):
    if 'db' in g:
        g.db.close()

    
@app.errorhandler(413)
def request_too_large(error):
    flash("The image is too large to save. Max size is {}MB".format(int(shotglass.get_site_config().get("MAX_CONTENT_LENGTH",".25"))/1048576))
    return redirect(url_for('bikematch.display'))


@app.errorhandler(404)
def page_not_found(error):
    return shotglass.page_not_found(error)

@app.errorhandler(500)
def server_error(error):
    return shotglass.server_error(error)

#Register the static route
app.add_url_rule('/static/<path:filename>','static',shotglass.static)

# To use a different subdomain as asset server, use this instead
# Direct to a specific server for static content
#app.add_url_rule('/static/<path:filename>','static',shotglass.static,subdomain="somesubdomain")


## Setup the routes for users
shotglass.register_users(app)

# setup www.routes...
# shotglass.register_www(app)
# from shotglass2.www.views import home
# app.add_url_rule('/contact/',home.contact)

from bikematch.views import bikematch, match, bike, recipient
app.register_blueprint(bikematch.mod)
app.register_blueprint(match.mod)
app.register_blueprint(bike.mod)
app.register_blueprint(recipient.mod)


if __name__ == '__main__':
    
    with app.app_context():
        # create the default database if needed
        initalize_all_tables()
        
    #app.run(host='localhost', port=8000)
    app.run()
    
    
## Site Settings

## Changes to this settings file only take effect after restarting the server ###

## ALL CONFIG NAMES MUST BE UPPERCASE!  ##

# The basics...
HOST_NAME = 'localhost:5000' 
SITE_NAME = "My New Web Site"
DEBUG = True

############################################
### You Must ABSOLUTELY change this key
############################################
SECRET_KEY = "somereallylongstringtouseasakey"

## Email Sending...
MAIL_SERVER = 'localhost'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = ""
MAIL_PASSWORD = ""

MAIL_SUBJECT_PREFIX = ''

MAIL_DEFAULT_SENDER = "Some Name"
MAIL_DEFAULT_ADDR = "admin@example.com"

CONTACT_NAME = MAIL_DEFAULT_SENDER
CONTACT_EMAIL_ADDR = MAIL_DEFAULT_ADDR

#Contact info for additional admins to inform
# A list of tuples: (recipient name,recipient address)
ADMIN_EMAILS = None #[(CONTACT_NAME,CONTACT_EMAIL_ADDR),]

CC_ADMIN_ON_CONTACT = True
ADMIN_ROLES = ['super','admin'] 

REPORT_404_ERRORS = DEBUG

# Security Settings
REQUIRE_SSL = (not DEBUG)

# Timezone setting
# This is the Time zone where you think you are,
# in case the server is in a different time zone.
# Un-comment one or add yours
# for full list see pytz.all_timezones

TIME_ZONE = 'US/Pacific'
#TIME_ZONE = 'US/Mountain'
#TIME_ZONE = 'US/Central'
#TIME_ZONE = 'US/Eastern'

# You can change database to another name if you like.
DATABASE_NAME= "database.sqlite"
DATABASE_PATH= 'instance/' + DATABASE_NAME

#############################################
### These settings are probably Ok...
#############################################

CGI_ROOT_FIX_APPLY = True # Some webservers mess up the root url
CGI_ROOT_FIX_PATH = "/" #this is usually correct path

if REQUIRE_SSL:
    HOST_PROTOCOL = "https"
else:
    HOST_PROTOCOL = "http"

# set session expiration
### Requires that session.permanent == True in request
from datetime import timedelta
PERMANENT_SESSION_LIFETIME = timedelta(days=31)

# Uploads ...
MAX_CONTENT_LENGTH = 1024 * 1024 * 4 # 4MB
UPLOAD_FOLDER = 'resource/static'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# settings for Main Nav Menu
MENU_AS_BAR = False #if True use Bar style main nav menu else sidebar by default
SUPPRESS_LOGIN_MENU_ITEM = False ## If True, don't display the login menu item

## some administrative settings
ALLOW_USERNAME_CHANGE = True
ALLOW_USER_SIGNUP = True #User may create their own accounts
#By default, user accounts are inactive untill approved by Admin.
ACTIVATE_USER_ON_CONFIRMATION=False #Activate when user responds to the confimation email
AUTOMATICALLY_ACTIVATE_NEW_USERS=True #no confirmation email sent.

## Places to look for documentation:
DOC_DIRECTORY_LIST = ['/','docs','shotglass2/','shotglass2/docs/',]

# Where to look for static files.
# after searching these directories without success,
# 'static' & 'shotglass2/static' are searched
# Must be a list.
STATIC_DIRS = [
    'resource/static',
]

## This list will be PREPENDED to the above static search
#### if you override this is SHARED_HOST_SETTINGS be sure to profide a list:
####.   'local_static_dirs': ['resource/local8000/static']
#LOCAL_STATIC_DIRS = [
#    'resource/localhost/static',
#]

## For Debuging
#EXPLAIN_TEMPLATE_LOADING = True

# Template directories to search FIRST
# Must be a list of app relative paths to search
HOST_TEMPLATE_DIRS = [
    'resource'
]

# Template directories to search AFTER HOST_TEMPLATE_DIRS
# Must be a list of app relative paths to search
TEMPLATE_DIRS = [
    'templates/www',
    'templates/users',
    ]
    
# After that search continues thru...
# app.template_folder (usually 'templates') then...
# 'shotglass2/templates' then...
# each blueprint in the order defined

    
# A list of dictionaries of settings for sites that share this config and virtualenv
SHARED_HOST_SETTINGS = [
    {"host_name": HOST_NAME, "database_path": DATABASE_PATH, "time_zone": TIME_ZONE, "contact_email_addr": CONTACT_EMAIL_ADDR, "contact_name": CONTACT_NAME},
    ]


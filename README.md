# SABA #BikeMatch

***Version 2***

This is a second attempt at the BikeMatch (and that's how I intend to spelling now...) web site and database.

Instead of the one-donor to one-recipient model envisioned by the originators of the BikeMatch scheme
we are going more for a bike shopping experience for recipients. They will pick a bike they would like to have
and the date and time that they will be coming to get it. We will meet them at the location we had designated 
and they come there (or not) and get their bike (or not).

## Installation 

A typical approach to setting up a new BikeMatch project would be to:
* clone the bikematch repo into your development machine:
    ```
    git clone https://github.com/wleddy/bikematch.git
    ```

* cd into the new directory and clone shotglass2 (required) into it with:
    ```
    git clone https://github.com/wleddy/shotglass2.git
    ```
    
* cd back to your bikematch directory.

* From the terminal run `. setup_env`  
  This will create the instance directory:
    * The 'instance' directory is where you'll keep your private info such as the encryption key and email account info. The database files
    are usually stored here too. You can use the file `default_site_settings.py` as a template. Copy or move it to the instance
    directory as `site_settings.py` and make changes as needed.
    
    * setup_env will also try to create virtualenv directory 'env' and pip the requirements into it.  

* You should now be in the virtual environment. If not, type `. activate_env` to activate it.
* Next, edit the file at `instance/site_settings.py` with all your secrets.
* Enter `python app.py` to start the dev server and create the initial database.

# SABA #BikeMatch

***UPDATE***: I've mothballed this effort in favor of [bikematch.safelanes.org](http://bikematch.safelanes.org) at [braitsch/bikematch](https://github.com/braitsch/bikematch).

This is primarily a simple set of contact forms to help us match bike donors to bike recipients.

You can use it just like that and deal with the responses off line as you see fit.

I have also added the ability to record information about the bikes and who gave and got them. 
Don't yet know if this is going to be useful to anyone, but it's there in a preliminary sort of
way.

You need to log in to see the Bike and "Folks" menu options to manage the records.


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

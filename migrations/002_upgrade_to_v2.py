"""
migrated data from the old data layout to version 2
"""
import sys
sys.path.append('') ##get import to look in the working dir.
import os
from shotglass2.takeabeltof.database import Database
from shotglass2.takeabeltof.file_upload import FileUpload

from bikematch import models as new_models
import v1_models as old_models
import pdb

def convert_size(bike_size):
    d = {'min_pedal_length':0,'max_pedal_length':0}
    sizes = {
    "4'10\"":25,
    "5'0\"":25.5,
    "5'2\"":26,
    "5'3\"":26.5,
    "5'4\"":27,
    "5'5\"":27.5,
    "5'6\"":28,
    "5'7\"":28.5,
    "5'8\"":29,
    "5'9\"":29.5,
    "5'10\"":30,
    "5'11\"":30.5,
    "6'0\"":31,
    "6'1\"":31.5,
    "6'2\"":32,
    }
    
    if bike_size in sizes:
        d = {"min_pedal_length":sizes[bike_size]-1,"max_pedal_length":sizes[bike_size]+1}
    
    return d
    
    
new_db = input("New database location? [instance/database_v2.sqlite]")
if not new_db:
    new_db = "instance/database_v2.sqlite"
    
print("======================================")
clear_new = input("Clear new data file first? {Y/n}")
if not clear_new or clear_new.upper()[0] not in "YN":
    print("     Set to delete new data file if exists")
    clear_new = True
else:
    clear_new = False
    
print("=====================================")
    
old_db = input("Old database location? [instance/database.sqlite]")
if not old_db:
    old_db = "instance/database.sqlite"
    
print("======================================")
if clear_new and os.path.exists(new_db):
    print("      Removing old data file")
    os.remove(new_db)
        
new_con = Database(new_db).connect()
new_models.init_all_bikematch_tables(new_con)
# add a temporary field to the new bike table to hold the old bike ID
new_con.execute("alter table bike add old_id INTEGER")

old_con = Database(old_db).connect()

print("======================================")
print("Moving bikes")

# move the bikes
new_bike = new_models.Bike(new_con)
new_folks = new_models.Folks(new_con)
bike_image = new_models.BikeImage(new_con)
donor_bike = new_models.DonorBike(new_con)

recs = old_models.Bike(old_con).select()
print("Moving {} bike records.".format(len(recs)))
for rec in recs:
    # copy bike
    new = new_bike.new()
    new.bike_comment = rec.bike_comment + " (original size: {})".format(rec.bike_size)
    new.staff_comment = rec.staff_comment
    new.bike_type = rec.bike_type
    new.created = rec.created
    new.old_id = rec.id
    sizes = convert_size(rec.bike_size)
    new.min_pedal_length = sizes["min_pedal_length"]
    new.max_pedal_length = sizes["max_pedal_length"]
    new_bike.save(new)
    
    # attach the image
    if rec.image_path:
        print(rec.image_path)
        upload = FileUpload(local_path="bikematch/bikes/{}".format(new.id))
        try:
            with open("resource/static/" + rec.image_path,'rb') as f:
                filename = rec.image_path[rec.image_path.rfind('/')+1:len(rec.image_path)]
                upload.save(f.read(),filename=filename)
            if upload.success:
                new_image = bike_image.new()
                new_image.bike_id = new.id
                new_image.image_path = upload.saved_file_path_string
                bike_image.save(new_image)
            else:
                print(upload.error_text)
        except:
            print("Failed to save {}".format(rec.image_path))
        
    # move donor to folks if needed
    folk = new_folks.select_one(where="first_name = '{}' and last_name = '{}'".format(rec.first_name,rec.last_name))
    if not folk:
        print("adding {} {}".format(rec.first_name,rec.last_name))
        folk = new_folks.new()
        folk.first_name = rec.first_name
        folk.last_name = rec.last_name
        folk.email = rec.email
        folk.phone = rec.phone
        new_folks.save(folk)
    # attach donor to new bike
    db = donor_bike.new()
    db.donor_id = folk.id
    db.bike_id = new.id
    donor_bike.save(db)
    
    new_con.commit()
    
# Move only the recipeints who have been matched
print("====================================")
recs = old_models.Match(old_con).select()
recipients = old_models.Recipient(old_con)
new_bikes = new_models.Bike(new_con)
print("Moving {} Matches".format(len(recs)))
print("====================================")
matches = new_models.Match(new_con)
# pdb.set_trace()
for rec in recs:
    # copy reipient to folks
    recipient = recipients.select_one(where="id = {}".format(rec.recipient_id))
    folk = new_folks.select_one(where="first_name = '{}' and last_name = '{}'".format(recipient.first_name,recipient.last_name))
    if not folk:
        print("adding {} {}".format(recipient.first_name,recipient.last_name))
        folk = new_folks.new()
        folk.first_name = recipient.first_name
        folk.last_name = recipient.last_name
        folk.email = recipient.email
        folk.phone = recipient.phone
        new_folks.save(folk)
    
    # link match to bike and folks
    new_match = matches.new()
    new_match.recipient_id = folk.id
    # the id of the old linked bike file was the bike ID
    bike = new_bikes.select_one(where="old_id = {}".format(rec.donor_id))
    new_match.bike_id = bike.id
    new_match.match_date = rec.match_date
    new_match.match_comment = rec.match_comment
    matches.save(new_match)
    
    new_con.commit()
    
#Remove the temp field from bike
new_con.execute("PRAGMA foreign_keys=OFF")
new_con.execute("""
CREATE TABLE IF NOT EXISTS 'temp_bike' (
            id INTEGER NOT NULL PRIMARY KEY,
            bike_comment TEXT,
            staff_comment TEXT,
            min_pedal_length NUMBER,
            max_pedal_length NUMBER,
            price FLOAT,
            bike_type TEXT,
            created DATETIME)
""")
new_con.execute("""insert into temp_bike 
             select id, 
             bike_comment ,
             staff_comment ,
             min_pedal_length ,
             max_pedal_length ,
             price ,
             bike_type ,
             created 
             
              from bike """)
              
new_con.execute("drop table bike")
new_con.execute("alter table temp_bike rename to bike")
new_con.execute("PRAGMA foreign_keys=ON")
new_con.commit()
    
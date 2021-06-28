"""
migrated data from the old data layout to version 2
"""
import sys
sys.path.append('') ##get import to look in the working dir.
import os
from shotglass2.takeabeltof.database import Database
from shotglass2.takeabeltof.file_upload import FileUpload
from shotglass2.takeabeltof.utils import formatted_phone_number
from shotglass2.takeabeltof.date_utils import local_datetime_now
from datetime import timedelta
from bikematch import models as new_models
import v1_models as old_models
import re
from PIL import Image
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
# pdb.set_trace()
cur = new_con.cursor()
for rec in recs:
    # copy bike
    #preserve the original ids
    cur.execute("insert into bike (id) values ({})".format(rec.id,))
    # pdb.set_trace()
    new = new_bike.new()
    new_bike.update(new,rec._asdict())
    # new = new_bike.get(rec.id)
    new.id = rec.id
    new.bike_comment = rec.bike_comment + " (original size: {})".format(rec.bike_size)
    # new.staff_comment = rec.staff_comment
    # new.bike_type = rec.bike_type
    # new.created = rec.created
    gears = re.findall("\s(\d*)\s?spd\.?", rec.bike_comment)
    if gears:
        new.number_of_gears = gears[0]
    else:
        new.number_of_gears = "?"
    make = ""
    f = re.search("([R|r]aleigh)|([S|s]chwinn)|([T|t]rek)|([S|s]pecialized)", rec.bike_comment)
    if f:
        make = rec.bike_comment[f.start():f.end()]
    new.make =  make
    sizes = convert_size(rec.bike_size)
    new.min_pedal_length = sizes["min_pedal_length"]
    new.max_pedal_length = sizes["max_pedal_length"]
    new_bike.save(new)
    
    # attach the image
    if rec.image_path:
        print(rec.image_path)
        local_path="bikematch/bikes/{}".format(new.id)
        resource_path = "resource/static/"
        upload = FileUpload(local_path=local_path)
        try:
            with open(resource_path + rec.image_path,'rb') as f:
                filename = rec.image_path[rec.image_path.rfind('/')+1:len(rec.image_path)]
                upload.save(f.read(),filename=filename) # moves the image to a new directory
                # make it a thumbnail
                max_size = 1000
                im = Image.open(resource_path + upload.saved_file_path_string)
                size = (im.height,im.width)
                if im.width > max_size or im.height > max_size:
                    size = (max_size,max_size)
                    im.thumbnail(size)
                    im.save(resource_path + upload.saved_file_path_string)
                    im.close()
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
    # keep all the bike kitchen records together (I was not consistent)
    if "kitchen" in rec.first_name.lower() or "kitchen" in rec.last_name.lower():
        rec.first_name = "Sacramento"
        rec.last_name = "Bicycle Kitchen"
    folk = new_folks.select_one(where="first_name = '{}' and last_name = '{}'".format(rec.first_name,rec.last_name))
    if not folk:
        print("adding {} {}".format(rec.first_name,rec.last_name))
        folk = new_folks.new()
        folk.first_name = rec.first_name
        folk.last_name = rec.last_name
        folk.email = rec.email
        folk.phone = formatted_phone_number(rec.phone)
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
        folk.phone = formatted_phone_number(recipient.phone)
        new_folks.save(folk)
    
    # link match to bike and folks
    new_match = matches.new()
    new_match.recipient_id = folk.id
    # the id of the old linked bike file was the bike ID
    bike = new_bikes.select_one(where="id = {}".format(rec.donor_id))
    new_match.bike_id = bike.id
    new_match.match_date = rec.match_date
    new_match.match_comment = rec.match_comment
    matches.save(new_match)
    
    new_con.commit()
    
# Just for grinsm, lets create some match days and the locatoin for SBK
location = new_models.Location(new_con)
rec = location.new()
rec.location_name = "Sacramento Area Bicycle Advocates"
rec.street_address = "909 12th Street"
rec.city = "Sacramento"
rec.state = "CA"
rec.zip = "95814"
rec.lng = "-121.4901"
rec.lat = "38.5802"
location.save(rec)
location.commit()

loc_id = rec.id

match_day = new_models.MatchDay(new_con)
start = local_datetime_now().replace(hour=10,minute=0,second=0)
for x in range(6):
    start = start + timedelta(days=7)
    rec = match_day.new()
    rec.start = start
    rec.number_of_slots = 8
    rec.slot_minutes = 15
    rec.location_id = loc_id
    match_day.save(rec)
match_day.commit()



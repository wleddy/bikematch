import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

from shotglass2.takeabeltof.database import Database
from bikematch.models import Bike, Match, Recipient

db = Database('instance/database.sqlite').connect()
db.execute("DROP TRIGGER IF EXISTS clear_match_before_delete")
db.execute("Drop table if exists bike")
Bike(db).init_table()
db.execute("Drop table if exists recipient")
Recipient(db).init_table()

sql = """
    insert into bike (
    id,
    first_name,
    last_name,
    email,
    city,
    zip,
    phone,
    neighborhood,
    created,
    status,
    bike_size,
    bike_type,
    bike_comment,
    image_path,
    staff_comment,
    match_id)
    
    select 
    folks.id,
    folks.first_name,
    folks.last_name,
    folks.email,
    folks.city,
    folks.zip,
    folks.phone,
    folks.neighborhood,
    folks.created,
    folks.status,
    folks.bike_size,
    folks.bike_type,
    folks.bike_comment,
    folks.image_path,
    folks.staff_comment,
    folks.match_id
    
    from folks where lower(folks.d_or_r) = 'donor'
    """
db.execute(sql)

sql = """
    insert into recipient (
    id,
    first_name,
    last_name,
    email,
    city,
    zip,
    phone,
    neighborhood,
    created,
    status,
    bike_size,
    bike_type,
    occupation,
    request_comment,
    staff_comment,
    priority,
    match_id
    )
    
    select 
    folks.id,
    folks.first_name,
    folks.last_name,
    folks.email,
    folks.city,
    folks.zip,
    folks.phone,
    folks.neighborhood,
    folks.created,
    folks.status,
    folks.bike_size,
    folks.bike_type,
    folks.occupation,
    folks.bike_comment,
    folks.staff_comment,
    folks.priority,
    folks.match_id
    
    from folks where lower(folks.d_or_r) <> 'donor'
    """
db.execute(sql)

# db.execute("drop table folks")

# restore delete triggers
Match(db).init_table()

db.commit()


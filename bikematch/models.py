from flask import g
from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.takeabeltof.date_utils import local_datetime_now
from datetime import timedelta


class Bike(SqliteTable):
    """Bikes for matching"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'bike'
        self.order_by_col = 'created'
        self.defaults = {'price':0,'price_is_fixed':0,'created':'now',}

    
    def create_table(self):        
        sql = """
            bike_comment TEXT,
            staff_comment TEXT,
            number_of_gears TEXT,
            min_pedal_length NUMBER,
            max_pedal_length NUMBER,
            price NUMBER,
            price_is_fixed INTEGER,
            bike_type TEXT,
            make TEXT,
            created DATE
            """
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
            # {'name':'status','definition':'TEXT',},
        """

        column_list = [
        ]

        return column_list
        

    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else '1'
        order_by = order_by if order_by else self.order_by_col
        
        from bikematch.views.bike import inseam_to_height
        self.db.create_function("inseam_to_height", 1, inseam_to_height)
        
        sql = """select distinct bike.*,
        bike.min_pedal_length ||'" ~ ' || bike.max_pedal_length || '"' as pedal_length,
        inseam_to_height(bike.min_pedal_length) as min_height,
        inseam_to_height(bike.max_pedal_length) as max_height,
        inseam_to_height(bike.min_pedal_length) || '~' || inseam_to_height(bike.max_pedal_length) as height,
        donor.first_name as donor_first_name,
        donor.last_name as donor_last_name,
        donor.first_name || ' ' || donor.last_name as donor_full_name,
        donor.id as donor_id,
        donor.email as donor_email,
        donor.phone as donor_phone,
        bike_image.image_path,
        CASE
            when match.id is not null then 'Matched'
            when reservation.id is not null then 'Reserved'
            else 'Available'
        END as bike_status,
        match.id as match_id,
        recipient.first_name || ' ' || recipient.last_name as recipient_full_name,
        recipient.email as recipient_email,
        recipient.phone as recipient_phone,
        match.match_date,
        match.match_comment,
        reservation.id as reservation_id,
        reservation.first_name || ' ' || reservation.last_name as reservation_full_name,
        reservation.email as reservation_email,
        reservation.phone as reservation_phone
        from bike
        left join match on match.bike_id = bike.id
        left join donor_bike on donor_bike.bike_id = bike.id
        left join folks as donor on donor.id = donor_bike.donor_id
        left join folks as recipient on recipient.id = match.recipient_id
        left join reservation on reservation.bike_id = bike.id
        left join bike_image on bike_image.bike_id = bike.id
        where {where}
        order by {order_by}
        """.format(where=where,order_by=order_by)

        return self.query(sql)

class Folks(SqliteTable):
    """People receiving and donating Bikes"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'folks'
        self.order_by_col = 'id'
        self.defaults = {}
    
    def create_table(self):        
        sql = """
            'first_name' TEXT,
            'last_name' TEXT,
            'email' TEXT,
            'phone' TEXT
            """
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        # {'name':'status','definition':'TEXT',},
        """

        column_list = [
        ]

        return column_list
        
    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else '1'
        order_by = order_by if order_by else self.order_by_col
        sql = """select folks.*,
            first_name || ' ' || last_name as full_name
            from folks
            where {where}
            order by {order_by}
            """.format(where=where,order_by=order_by)
            
        return self.query(sql)
        

class Match(SqliteTable):
    """Record bike matches"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'match'
        self.order_by_col = 'match_date'
        self.defaults = {'payment_amt':0.0,'match_date':'now'}
        self._display_name = "Match"
        
    def create_table(self):
        """Define and create the role table"""
        
        sql = """
            bike_id INT ,
            recipient_id INT ,
            match_date DATE,
            payment_amt FLOAT,
            match_comment TEXT,
            due_date DATE,
            FOREIGN KEY (bike_id) REFERENCES bike(id) ON DELETE CASCADE,
            FOREIGN KEY (recipient_id) REFERENCES folks(id) ON DELETE CASCADE 
            """
        super().create_table(sql)

    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else 1
        order_by = order_by if order_by else self.order_by_col
        sql = """select match.*,
        donor.first_name as donor_first_name,
        donor.last_name as donor_last_name,
        donor.first_name || ' ' || donor.last_name as donor_name,
        donor.id as donor_id,
        donor.email as donor_email,
        donor.phone as donor_phone,
        recipient.first_name as recipient_first_name,
        recipient.last_name as recipient_last_name,
        recipient.first_name || ' ' || recipient.last_name as recipient_name,
        recipient.email as recipient_email,
        recipient.phone as recipient_phone,
        (select image_path from bike_image where bike_id = match.bike_id limit 1) as image_path,
        bike.bike_comment,
        bike.price,
        bike.created as donation_date
        from match
        left join donor_bike on donor_bike.bike_id = match.bike_id
        left join folks as donor on donor_bike.donor_id = donor.id
        left join folks as recipient on recipient.id = match.recipient_id
        left join bike on bike.id = match.bike_id
        where {where}
        order by {order_by}
        """.format(where=where,order_by=order_by)

        return self.query(sql)


class DonorBike(SqliteTable):
    """Reference table for folks and donated bikes"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'donor_bike'
        self.order_by_col = 'id'
        self.defaults = {}


    def create_table(self):        
        sql = """
            bike_id INTEGER,
            donor_id INTEGER,
            FOREIGN KEY (bike_id) REFERENCES bike(id) ON DELETE CASCADE,
            FOREIGN KEY (donor_id) REFERENCES folks(id) ON DELETE CASCADE 
            """
        super().create_table(sql)


class BikeImage(SqliteTable):
    """Refers to image locations for a bike record"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'bike_image'
        self.order_by_col = 'id'
        self.defaults = {}


    def create_table(self):        
        sql = """
            bike_id INTEGER,
            image_path TEXT,
            FOREIGN KEY (bike_id) REFERENCES bike(id) ON DELETE CASCADE 
            """
        super().create_table(sql)


class MatchImage(SqliteTable):
    """Refers to image locations for a match record"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'match_image'
        self.order_by_col = 'id'
        self.defaults = {}


    def create_table(self):        
        sql = """
            match_id INTEGER,
            image_path TEXT,
            FOREIGN KEY (match_id) REFERENCES match(id) ON DELETE CASCADE 
            """
        super().create_table(sql)
        

class Reservation(SqliteTable):
    """Refers to image locations for a bike record"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'reservation'
        self.order_by_col = 'reservation_date'
        self.defaults = {}


    def create_table(self):        
        sql = """
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            reservation_date DATETIME,
            payment NUMBER,
            match_day_id INTEGER,
            bike_id INTEGER
            """
        super().create_table(sql)

    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else 1
        order_by = order_by if order_by else self.order_by_col
        sql = """select reservation.*,
        reservation.first_name || ' ' || reservation.last_name as full_name,
        location.location_name,
        location.street_address,
        location.city,
        location.state,
        location.zip,
        location.lng,
        location.lat,
        CASE
            when match.id is not null then 'Matched'
            when reservation.id is not null then 'Reserved'
            else 'Available'
        END as bike_status,
        match.id as match_id,
        match_day.start,
        bike.price,
        bike.price_is_fixed
        
        from reservation
        left join match_day on match_day.id = reservation.match_day_id
        left join bike on bike.id = reservation.bike_id
        left join location on location.id = match_day.location_id
        left join match on match.bike_id = reservation.bike_id
        where {where}
        order by {order_by}
        """.format(where=where,order_by=order_by)

        return self.query(sql)


class MatchDay(SqliteTable):
    """A list of dates, times and locations where we intend to make matches"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'match_day'
        self.order_by_col = 'start'
        self.defaults = {}


    def create_table(self):        
        sql = """
            start DATETIME,
            number_of_slots INTEGER,
            slot_minutes INTEGER,
            location_id INTEGER
            """
        super().create_table(sql)

    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else 1
        order_by = order_by if order_by else self.order_by_col
        sql = """select match_day.*,
        location.location_name
        from match_day
        left join location on location.id = match_day.location_id
        where {where}
        order by {order_by}
        """.format(where=where,order_by=order_by)

        return self.query(sql)
        
    def select_future(self):
        """Select all future handoff events"""
        
        # if it's after 6pm the first record must start AFTER tomorrow
        start_limit = local_datetime_now()
        if start_limit.hour >=18:
            start_limit = start_limit + timedelta(days=1)
            
        where = "date(start,'localtime') > date('{}','localtime')".format(start_limit)
        
        return self.select(where=where)
        

class Location(SqliteTable):
    """Staffing Location Table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'location'
        self.order_by_col = 'lower(location_name), id'
        self.defaults = {}

    def create_table(self):
        """Define and create the table"""

        sql = """
        location_name TEXT NOT NULL,
        street_address TEXT,
        city  TEXT,
        state  TEXT,
        zip TEXT,
        lat  NUMBER,
        lng  NUMBER
        """
        
        super().create_table(sql)


def init_all_bikematch_tables(db):
    Folks(db).init_table()
    Match(db).init_table()
    Bike(db).init_table()
    MatchDay(db).init_table()
    DonorBike(db).init_table()
    BikeImage(db).init_table()
    MatchImage(db).init_table()
    Reservation(db).init_table()
    Location(db).init_table()
    
    

from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.users.views.password import getPasswordHash
        

class DonorsAndRecipients(SqliteTable):
    """Bike Donors and Recipients"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'donors_and_recipients'
        self.order_by_col = 'lower(last_name), lower(first_name)'
        self.defaults = {}
        self._display_name = "Donors & Recipients"
    
    def create_table(self):        
        sql = """
            'first_name' TEXT,
            'last_name' TEXT,
            'email' TEXT,
            'city' TEXT,
            'state' TEXT,
            'zip' TEXT,
            'neighborhood' TEXT,
            'contact_type' TEXT,
            'created' DATETIME,
            'bike_size' TEXT,
            'bike_type' TEXT,
            'bike_comment' TEXT,
            'image_path' TEXT,
            'staff_comment' TEXT,
            'match_id' INT
            """
        super().create_table(sql)
        
        
    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else 'match_id is null'
        order_by = order_by if order_by else self.order_by_col
        sql = """select donors_and_recipients.*,
        donors_and_recipients.first_name || ' ' || donors_and_recipients.last_name as full_name,
        match.match_date,
        match.match_status,
        match.match_comment
        from donors_and_recipients
        left join match on match.id = donors_and_recipients.match_id
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
        self.defaults = {}
        self._display_name = "Match"
        
    def create_table(self):
        """Define and create the role tablel"""
        
        sql = """
            'donor_id' INT ,
            'recipient_id' INT ,
            'match_date' DATETIME,
            'match_status' TEXT,
            'match_comment' TEXT
             """
        super().create_table(sql)


    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else 1
        order_by = order_by if order_by else self.order_by_col
        sql = """select match.*,
        donor.first_name as donor_first_name,
        donor.last_name as donor_last_name,
        recipient.first_name as recipient_first_name,
        recipient.last_name as recipient_last_name
        from match
        left join donors_and_recipients as donor on donor.id = match.donor_id 
        left join donors_and_recipients as recipient on recipient.id = match.recipient_id
        where {where}
        order by {order_by}
        """.format(where=where,order_by=order_by)
        
        return self.query(sql)

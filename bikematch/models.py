from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.users.views.password import getPasswordHash
        
class Bike(SqliteTable):
    """Handle some basic interactions with the role table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'bike'
        self.order_by_col = 'id'
        self.defaults = {}
        
    def create_table(self):
        """Define and create the role tablel"""
        
        sql = """
            'donor_id' INT ,
            'donation_date' DATE,
            'recipient_id' INT ,
            'delivery_date' DATE,
            'bike_description' TEXT,
            'serial_number' TEXT,
            'image_path' TEXT
             """
        super().create_table(sql)


    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else 1
        order_by = order_by if order_by else self.order_by_col
        sql = """select bike.*,
        donor.first_name as donor_first_name,
        donor.last_name as donor_last_name,
        recipient.first_name as recipient_first_name,
        recipient.last_name as recipient_last_name
        from bike
        left join folks as donor on donor.id = bike.donor_id 
        left join folks as recipient on recipient.id = bike.recipient_id
        where {where}
        order by {order_by}
        """.format(where=where,order_by=order_by)
        
        return self.query(sql)

class Folks(SqliteTable):
    """Bike Donors and Recipients"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'folks'
        self.order_by_col = 'lower(last_name), lower(first_name)'
        self.defaults = {}
    
    
    def create_table(self):        
        sql = """
            'first_name' TEXT,
            'last_name' TEXT,
            'email' TEXT,
            'phone' TEXT,
            'address' TEXT,
            'address2' TEXT,
            'city' TEXT,
            'state' TEXT,
            'zip' TEXT,
            'comment' TEXT,
            'donor_or_recipient' TEXT,
            'date_created' DATE
            """
        super().create_table(sql)
        
        
    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else 1
        order_by = order_by if order_by else self.order_by_col
        sql = """select folks.*,
        bike.delivery_date
        from folks
        left join bike on folks.id = bike.recipient_id
        where {where}
        order by {order_by}
        """.format(where=where,order_by=order_by)
    
        return self.query(sql)

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
            'donor_name' TEXT ,
            'donor_email' TEXT ,
            'donor_comment' TEXT ,
            'donation_date' DATE,
            'recipient_name' TEXT ,
            'recipient_email' TEXT ,
            'recipient_comment' TEXT ,
            'delivery_date' DATE,
            'bike_description' TEXT,
            'serial_number' TEXT,
            'image_path' TEXT """
        super().create_table(sql)

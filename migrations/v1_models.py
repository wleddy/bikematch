from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.users.views.password import getPasswordHash
  
  
class Bike(SqliteTable):
    """Bike Donors and Recipients"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'bike'
        self.order_by_col = 'created'
        self.defaults = {'status':'Open'}

    
    def create_table(self):        
        sql = """
            'first_name' TEXT,
            'last_name' TEXT,
            'email' TEXT,
            'city' TEXT,
            'zip' TEXT,
            'phone' TEXT,
            'neighborhood' TEXT,
            'created' DATETIME,
            'status' TEXT,
            'bike_size' TEXT,
            'bike_type' TEXT,
            'bike_comment' TEXT,
            'image_path' TEXT,
            'staff_comment' TEXT,
            'match_id' INT
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
        

    # def select(self,where=None,order_by=None,**kwargs):
    #     where = where if where else 'match_id is null'
    #     order_by = order_by if order_by else self.order_by_col
    #     sql = """select bike.*,
    #     bike.first_name || ' ' || bike.last_name as full_name,
    #     match.match_date,
    #     match.match_status,
    #     match.match_comment
    #     from bike
    #     left join match on match.id = bike.match_id
    #     where {where}
    #     order by {order_by}
    #     """.format(where=where,order_by=order_by)
    #
    #     return self.query(sql)

class Recipient(SqliteTable):
    """People Requesting Bikes"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'recipient'
        self.order_by_col = 'created'
        self.defaults = {'status':'Open'}
    
    def create_table(self):        
        # sql = """
        #     'first_name' TEXT,
        #     'last_name' TEXT,
        #     'email' TEXT,
        #     'city' TEXT,
        #     'zip' TEXT,
        #     'phone' TEXT,
        #     'neighborhood' TEXT,
        #     'd_or_r' TEXT,
        #     'created' DATETIME,
        #     'bike_size' TEXT,
        #     'bike_type' TEXT,
        #     'occupation' TEXT,
        #     'bike_comment' TEXT,
        #     'image_path' TEXT,
        #     'staff_comment' TEXT,
        #     'priority' TEXT,
        #     'match_id' INT
        #     """
        sql = """
            'first_name' TEXT,
            'last_name' TEXT,
            'email' TEXT,
            'city' TEXT,
            'zip' TEXT,
            'phone' TEXT,
            'neighborhood' TEXT,
            'created' DATETIME,
            'status' TEXT,
            'bike_size' TEXT,
            'bike_type' TEXT,
            'occupation' TEXT,
            'request_comment' TEXT,
            'staff_comment' TEXT,
            'priority' TEXT,
            'match_id' INT
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
        
        
    # def select(self,where=None,order_by=None,**kwargs):
#         where = where if where else 'match_id is null'
#         order_by = order_by if order_by else self.order_by_col
#         sql = """select recipient.*,
#         recipient.first_name || ' ' || recipient.last_name as full_name,
#         match.match_date,
#         match.match_status,
#         match.match_comment
#         from recipient
#         left join match on match.id = recipient.match_id
#         where {where}
#         order by {order_by}
#         """.format(where=where,order_by=order_by)
#
#         return self.query(sql)


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
            'match_comment' TEXT,
            'match_image_path' TEXT
             """
        super().create_table(sql)
        
        # add a trigger to clear the match_id from Recipient
        sql = """CREATE TRIGGER IF NOT EXISTS 
        clear_match_before_delete BEFORE DELETE ON {this_table}
        BEGIN
        UPDATE recipient SET 
            match_id = NULL,
            status = 'Open'
        WHERE match_id = OLD.id;
        UPDATE bike SET 
            match_id = NULL,
            status = 'Open'
        WHERE match_id = OLD.id;
        END;
        """.format(this_table=self.table_name)
        self.db.execute(sql)


    # def select(self,where=None,order_by=None,**kwargs):
    #     where = where if where else 1
    #     order_by = order_by if order_by else self.order_by_col
    #     sql = """select match.*,
    #     donor.first_name as donor_first_name,
    #     donor.last_name as donor_last_name,
    #     donor.first_name || ' ' || donor.last_name as donor_name,
    #     recipient.first_name as recipient_first_name,
    #     recipient.last_name as recipient_last_name,
    #     recipient.first_name || ' ' || recipient.last_name as recipient_name
    #     from match
    #     left join bike as donor on donor.id = match.donor_id
    #     left join recipient as recipient on recipient.id = match.recipient_id
    #     where {where}
    #     order by {order_by}
    #     """.format(where=where,order_by=order_by)
    #
    #     return self.query(sql)

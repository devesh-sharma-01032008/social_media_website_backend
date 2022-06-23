from pymongo import mongo_client

client = mongo_client.MongoClient("mongodb://127.0.0.1:27017/")

mydb = client["user_details"]

information = mydb.Userinformation

user_schema = {
    "username": {"type": "string", "minlength": 1, "required": True},
    "email": {
        "type": "string",
        "required": True,
    },
    "mobile_number": {"type": "integer", "required": True, "unique": True},
    "password": {"type": "string", "required": True},
    "avatar": {"type": "string", "required": False},
}

information.insert_one(user_schema)


class MongoController:
    def __init__(self, uri, db_name, collection_name, admin_name, admin_passwd):
        """
        Usage:  Constructor to set all the value of this class

        RETURNS : None

        URI : it is the url to connect to mongodb e.g localhost:2000/

        DB_NAME : it is the name of database you want to use

        COLLECTION_NAME : it is the name of collection you want to use

        ADMIN_NAME : name of the administrator which can see all the records of database

        ADMIN_PASSWD : password for authorizing the admin

        NOTE: make sure to use environment variables for setting value in  this field
        """
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.admin_name = admin_name
        self.admin_passwd = admin_passwd
        self.start = 0

    def change_collection(self, new_collection_name):
        """
        Usage: This function help in changing the value of collection_name and switching collection

        RETURNS : None

        NEW_COLLECTION_NAME: new name of collection you are working with
        """
        self.collection_name = new_collection_name
        self.collection = self.db.get_collection(new_collection_name)

    def connect_to_mongo(self):
        """
        Usage: This function connects to database

        RETURNS : None
        """
        self.client = mongo_client.MongoClient(self.uri)
        self.db = self.client.get_database(self.db_name)

    def set_collection(self):
        """
        Usage : This function sets the value of collection for the class
        """
        self.connect_to_mongo()
        self.collection = self.db.get_collection(self.collection_name)

    def insert_data_in_collection(self, data):
        """
        Usage : It is used to add new data to collection without checking if it already exists.

        RETURNS : None
        """
        self.set_collection()
        is_inserted = self.collection.insert_one(data).acknowledged
        return is_inserted

    def insert_unique_data_in_collection(self, data, key=None):
        """
        Usage : It is used to add new data to collection if it already exists.

        DATA : data to be inserted

        KEY : value to identifty unique elements

        RETURNS : True if data is inserted else returns False if the given data already exists.
        """
        if key == None:
            key = data
        self.set_collection()
        if key != data:
            is_data_already = self.collection.find_one({key: data[key]})
        else:
            is_data_already = self.collection.find_one(data)
        if is_data_already:
            return False
        else:
            is_inserted = self.collection.insert_one(data).acknowledged
            return is_inserted

    def update_data_in_collection(self, data, new_data, key=None):
        if key == None:
            key = data
        self.set_collection()
        if key != data:
            is_updated = self.collection.find_one_and_update({key: data[key]}, new_data)
        else:
            is_updated = self.collection.find_one_and_update(data, new_data)
        return is_updated

    def delete_data_in_collection(self, data, key=None):
        """
        Usage : It is used to delete data from collection.

        DATA : data to be deleted

        KEY : value to identifty unique elements

        RETURNS : True if data is deleted data sucessfully else returns False no such data exists.
        """
        if key == None:
            key = data
        self.set_collection()
        if key != data:
            result = self.collection.find_one_and_delete({key: data[key]})
        else:
            result = self.collection.find_one_and_delete(data)
        return result

    def search(self, data):
        """
        Usage : It returns the data from mongodb if its member match with data given

        DATA : it is data to search in database
        """
        self.set_collection()
        result = self.collection.find_one(data)
        return result

    def get_some_data(self, count, hide_fields=["_id"]):
        self.set_collection()
        result = []
        for x in self.collection.find():
            required = {}
            for key in x:
                if key in hide_fields:
                    continue
                else:
                    required[key] = x[key]
            result.append(required)
        try:
            result = result[self.start:self.start+count]
            self.start += count
            print(result)
            print(self.start)
            if self.start > len(result):
                self.start = 0
            return result
            
        except Exception as e:
            print(e)
            return result

    def search_collection(self,collection_name):
        self.connect_to_mongo()
        self.all_collections = self.db.list_collection_names()
        if collection_name in self.all_collections:
            return True
        return False

    def create_collection(self,collection_name,initial_data={"name":""}):
        self.change_collection(collection_name)
        self.insert_data_in_collection(initial_data)

# creates a collection in database
# db = MongoController("mongodb://localhost:27017","JNV_Media","user_details","root","")
# db.connect_to_mongo()
# db.create_collection("devesh",{
#     "name":"devesh"
# })

# checks if collection exists in  the database
# print(db.search_collection("deveshs"))
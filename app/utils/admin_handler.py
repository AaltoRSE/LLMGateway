import pymongo
import json
import os
import urllib
import logging


testing = False
if "PYTEST_CURRENT_TEST" in os.environ:
    testig = True


adminLogger = logging.getLogger(__name__)


class AdminHandler:
    def __init__(self):
        if not testing:
            # Needs to be escaped if necessary
            mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER"))
            mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD"))

            mongo_URL = os.environ.get("MONGOHOST")
            # Set up required endpoints.
            mongo_client = pymongo.MongoClient(
                "mongodb://%s:%s@%s/" % (mongo_user, mongo_password, mongo_URL)
            )
            self.setup(mongo_client)

    def setup(self, mongo_client: pymongo.MongoClient):
        self.mongo_client = mongo_client
        self.db = mongo_client["gateway"]
        self.admin_collection = self.db["admins"]

    def is_admin(self, admin_id: str):
        """
        Test, whether the given user is an admin user
        Parameters:
        - admin_id (str): The user id of the user to test
        """
        exists = self.admin_collection.find_one({"userId": admin_id})
        if exists:
            return True
        else:
            return False

    def add_admin(self, admin_id: str):
        """
        Add a new admin user
        Parameters:
        - admin_id (str): The user id of the new admin user
        """
        exists = self.admin_collection.find_one({"userId": admin_id})
        if not exists:
            self.admin_collection.insert_one({"userId": admin_id})

    def delete_admin(self, admin_id: str):
        """
        Remove an admin user
        Parameters:
        - admin_id (str): The user id of the new admin user
        """
        self.admin_collection.delete_one({"userId": admin_id})

    def list_admins(self):
        return list(self.admin_collection.find({}, {"_id": 0, "userId": 1}))

    def list_users(self):
        pipeline = [
            {
                "$lookup": {
                    "from": "apikeys",
                    "localField": "source",
                    "foreignField": "key",
                    "as": "key_info",
                }
            },
            {
                "$addFields": {
                    "user": {
                        "$cond": {
                            "if": {"$eq": ["$sourcetype", "user"]},
                            "then": "$source",
                            "else": {"$arrayElemAt": ["$key_info.user", 0]},
                        }
                    }
                }
            },
            {"$group": {"_id": "$user"}},
        ]
        # Execute the aggregation pipeline
        result = list(self.db["logs"].aggregate(pipeline))
        # Extract the list of unique users
        return [entry["_id"] for entry in result]


if not testing:
    admin_handler = AdminHandler()

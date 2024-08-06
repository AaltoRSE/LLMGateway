import pymongo
import json
import os
import urllib
import logging
from fastapi import HTTPException

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
        existing_users = self.list_users()
        if not exists and admin_id in existing_users:
            self.admin_collection.insert_one({"userId": admin_id})
        if not admin_id in existing_users:
            raise HTTPException(400, "User does not exist")

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
                "$group": {
                    "_id": "$user",
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "user": "$_id",
                }
            },
        ]
        # Execute the aggregation pipeline
        result = list(self.db["apikeys"].aggregate(pipeline))
        # Extract the list of unique users
        return [entry["user"] for entry in result]


if not testing:
    admin_handler = AdminHandler()

import pymongo
from datetime import datetime
import os
import urllib


# Needs to be escaped if necessary
class logging_handler:
    def __init__(self, testing=False):
        if not testing:
            mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER"))
            mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD"))
            # Set up required endpoints.
            mongo_client = pymongo.MongoClient(
                "mongodb://%s:%s@mongo:27017/" % (mongo_user, mongo_password)
            )
            self.setup(mongo_client)

    def setup(self, mongo_client):
        self.db = mongo_client["gateway"]
        self.logCollection = self.db["logs"]
        self.userCollection = self.db["users"]

    def create_log_entry(self, tokencount, model, source, sourcetype="apikey"):
        """
        Function to create a log entry.

        Parameters:
        - tokencount (int): The count of tokens.
        - model (str): The model related to the log entry.
        - source (str): The source of the log entry.
        - sourcetype (str): The type of source either apikey or user..

        Returns:
        - dict: A dictionary representing the log entry with timestamp.
        """
        return {
            "tokencount": tokencount,
            "model": model,
            "source": source,
            "sourcetype": sourcetype,
            "timestamp": datetime.utcnow(),  # Current timestamp in UTC
        }

    def log_usage_for_key(self, tokencount, model, key):
        """
        Function to log usage for a specific key.

        Parameters:
        - tokencount (int): The count of tokens used.
        - model (str): The model associated with the usage.
        - key (str): The key for which the usage is logged.
        """
        logEntry = self.create_log_entry(tokencount, model, key)
        self.logCollection.insert_one(logEntry)

    def log_usage_for_user(self, tokencount, model, user):
        """
        Function to log usage for a specific user.

        Parameters:
        - tokencount (int): The count of tokens used.
        - model (str): The model associated with the usage.
        - user (str): The user for which the usage is logged.
        """
        logEntry = self.create_log_entry(tokencount, model, user, "user")
        self.logCollection.insert_one(logEntry)

    def get_usage_for_user(self, username):
        # Needs to be implemented
        pass

    def get_usage_for_key(self, key):
        # TODO: needs to be implemented
        pass

    def get_usage_for_model(self, model):
        # TODO: needs to be implemented
        pass

    def get_usage_for_timerange(self, start, end):
        # TODO: needs to be implemented
        pass

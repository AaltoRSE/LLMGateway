import pymongo
from datetime import datetime
import os
import urllib


# Needs to be escaped if necessary
class LoggingHandler:
    def __init__(self, testing=False):
        if not testing:
            mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER"))
            mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD"))
            mongo_URL = os.environ.get("MONGOHOST")
            # Set up required endpoints.
            mongo_client = pymongo.MongoClient(
                "mongodb://%s:%s@%s/" % (mongo_user, mongo_password, mongo_URL)
            )
            self.setup(mongo_client)

    def setup(self, mongo_client):
        self.db = mongo_client["gateway"]
        self.log_collection = self.db["logs"]
        self.user_collection = self.db["users"]

    def create_log_entry(self, tokencount, model, source, sourcetype="apikey"):
        """
        Function to create a log entry.

        Parameters:
        - tokencount (int): The count of tokens.
        - model (str): The model related to the log entry.
        - source (str): The source that authorized the request that is being logged. This could be a user name or an apikey.
        - sourcetype (str): Specification of what kind of source authorized the request that is being logged (either 'apikey' or 'user').

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
        log_entry = self.create_log_entry(
            tokencount=tokencount, model=model, source=key
        )
        self.log_collection.insert_one(log_entry)

    def log_usage_for_user(self, tokencount, model, user):
        """
        Function to log usage for a specific user.

        Parameters:
        - tokencount (int): The count of tokens used.
        - model (str): The model associated with the usage.
        - user (str): The user for which the usage is logged.
        """
        log_entry = self.create_log_entry(
            tokencount=tokencount, model=model, source=user, sourcetype="user"
        )
        self.log_collection.insert_one(log_entry)

    def get_usage_for_user(self, username):
        raise NotImplementedError

    def get_usage_for_key(self, key):
        raise NotImplementedError

    def get_usage_for_model(self, model):
        raise NotImplementedError

    def get_usage_for_timerange(self, start, end):
        raise NotImplementedError

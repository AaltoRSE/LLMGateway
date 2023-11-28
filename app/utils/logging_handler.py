import pymongo
from datetime import datetime
import os
import urllib

# Needs to be escaped if necessary
mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER"))
mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD"))

# Set up required endpoints.
mongo_client = pymongo.MongoClient(
    "mongodb://%s:%s@mongo:27017/" % (mongo_user, mongo_password)
)
db = mongo_client["gateway"]
logCollection = db["logs"]
userCollection = db["users"]


def create_log_entry(tokencount, model, source, sourcetype="apikey"):
    """
    Function to create a log entry.

    Parameters:
    - tokencount (int): The count of tokens.
    - model (str): The model related to the log entry.
    - source (str): The source of the log entry.
    - sourcetype (str): The type of source..

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


def log_usage_for_key(tokencount, model, key):
    """
    Function to log usage for a specific key.

    Parameters:
    - tokencount (int): The count of tokens used.
    - model (str): The model associated with the usage.
    - key (str): The key for which the usage is logged.
    """
    logEntry = create_log_entry(tokencount, model, key)
    logCollection.insert_one(logEntry)


def log_usage_for_user(tokencount, model, user):
    """
    Function to log usage for a specific user.

    Parameters:
    - tokencount (int): The count of tokens used.
    - model (str): The model associated with the usage.
    - user (str): The user for which the usage is logged.
    """
    logEntry = create_log_entry(tokencount, model, user, "user")
    logCollection.insert_one(logEntry)


def get_usage_for_user(username):
    # Needs to be implemented
    pass


def get_usage_for_key(key):
    # TODO: needs to be implemented
    pass


def get_usage_for_model(model):
    # TODO: needs to be implemented
    pass


def get_usage_for_timerange(start, end):
    # TODO: needs to be implemented
    pass

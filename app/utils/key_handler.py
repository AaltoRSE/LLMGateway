import redis
import pymongo
import secrets
import string
import os
import urllib

# Needs to be escaped if necessary
mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER"))
mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD"))

# Set up required endpoints. The
redis_client = redis.StrictRedis(host="redis", port=6379, db=0)
mongo_client = pymongo.MongoClient(
    "mongodb://%s:%s@mongo:27017/" % (mongo_user, mongo_password)
)
db = mongo_client["gateway"]
keyCollection = db["apikeys"]
# Make sure, that key is an index (avoids duplicates);
indices = keyCollection.create_index("key")
userCollection = db["users"]


def generate_api_key(length=64):
    """
    Function to generate an API key.

    Parameters:
    - length (int, optional): Length of the generated API key. Defaults to 64.

    Returns:
    - str: The generated API key.
    """
    alphabet = string.ascii_letters + string.digits
    api_key = "".join(secrets.choice(alphabet) for _ in range(length))
    return api_key


def build_new_key_object(key, name):
    """
    Function to create a new key object.

    Parameters:
    - key (str): The key value.
    - name (str): The name associated with the key.

    Returns:
    - dict: A dictionary representing the key object with "active" status, key, and name.
    """
    return {"active": True, "key": key, "name": name}


def check_key(key):
    """
    Function to check if a key currently exists

    Parameters:
    - key (str): The key to check.

    Returns:
    - bool: True if the key exists
    """
    return redis_client.sismember("keys", key)


def create_key(user, name):
    """
    Function to create a new key associated with a user.

    Parameters:
    - user (str): The username for which the key is created.
    - name (str): The name associated with the key.

    Returns:
    - str: The generated API key.
    """
    keyCreated = False
    api_key = ""
    while not keyCreated:
        api_key = generate_api_key()
        found = keyCollection.find_one({"key": api_key})
        if found == None:
            keyCollection.insert_one(build_new_key_object(api_key, name))
            userCollection.find_one_and_update(
                {"username": user}, {"$push", {"keys": api_key}}
            )
            keyCreated = True
    return api_key

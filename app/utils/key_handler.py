import redis
import pymongo
import secrets
import string
import os
import urllib


class key_handler:
    def __init__(self, testing: bool = False):
        if not testing:
            # Needs to be escaped if necessary
            mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER"))
            mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD"))

            # Set up required endpoints. The
            mongo_client = pymongo.MongoClient(
                "mongodb://%s:%s@mongo:27017/" % (mongo_user, mongo_password)
            )
            redis_client = redis.StrictRedis(host="redis", port=6379, db=0)
            self.setup(mongo_client, redis_client)

    def setup(self, mongo_client: pymongo.MongoClient, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.mongo_client = mongo_client
        self.db = mongo_client["gateway"]
        self.keyCollection = self.db["apikeys"]
        keyindices = self.keyCollection.index_information()
        # Make sure, that key is an index (avoids duplicates);
        if not "key" in keyindices:
            self.keyCollection.create_index("key")
        self.userCollection = self.db["users"]
        # Make sure, that username is an index (avoids duplicates when creating keys, which automatically adds a user if necessary);
        userindices = self.userCollection.index_information()
        if not "username" in userindices:
            self.userCollection.create_index("username")
        self.userCollection.find

    def generate_api_key(self, length: int = 64):
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

    def build_new_key_object(self, key: string, name: string):
        """
        Function to create a new key object.

        Parameters:
        - key (str): The key value.
        - name (str): The name associated with the key.

        Returns:
        - dict: A dictionary representing the key object with "active" status, key, and name.
        """
        return {"active": True, "key": key, "name": name}

    def check_key(self, key: string):
        """
        Function to check if a key currently exists

        Parameters:
        - key (str): The key to check.

        Returns:
        - bool: True if the key exists
        """
        return self.redis_client.sismember("keys", key)

    def delete_key(self, key: string, user: string):
        """
        Function to delete an existing key

        Parameters:
        - key (str): The key to check.
        - user (str): The user that requests this deletion

        """
        updated_user = self.userCollection.find_one_and_update(
            {"username": user, "keys": {"$elemMatch": {"$eq": key}}},
            {"$pull": {"keys": key}},
        )
        if not updated_user == None:
            # We found, and updated the user, so we can remove the key
            # removal should be instantaneous
            self.keyCollection.delete_one({"key": key})
            self.redis_client.srem("keys", key)

    def set_key_activity(self, key: string, user: string, active: bool):
        """
        Function to set the activity of a key

        Parameters:
        - key (str): The key to check.
        - user (str): The user that requests this deletion
        - active (bool): whether to activate or deactivate the key
        """
        user_has_key = self.userCollection.find_one(
            {"username": user, "keys": {"$elemMatch": {"$eq": key}}}
        )
        if not user_has_key == None:
            # the requesting user has access to this key
            self.keyCollection.update_one({"key": key}, {"$set": {"active": active}})
            if active:
                self.redis_client.sadd("keys", key)
            else:
                self.redis_client.srem("keys", key)

    def create_key(self, user: string, name: string):
        """
        Generates a unique API key and associates it with a specified user.

        Args:
        - user: Username of the user to whom the API key will be associated.
        - name: Name or label for the API key.
        - userCollection: Collection object representing the 'users' collection in MongoDB (default: global variable).
        - keyCollection: Collection object representing the 'apikeys' collection in MongoDB (default: global variable).

        Returns:
        - api_key: The generated unique API key associated with the user.
        """
        keyCreated = False
        api_key = ""
        while not keyCreated:
            api_key = self.generate_api_key()
            found = self.keyCollection.find_one({"key": api_key})
            if found == None:
                self.keyCollection.insert_one(self.build_new_key_object(api_key, name))
                self.userCollection.update_one(
                    {"username": user}, {"$addToSet": {"keys": api_key}}, upsert=True
                )
                self.redis_client.sadd("keys", api_key)
                keyCreated = True
        return api_key

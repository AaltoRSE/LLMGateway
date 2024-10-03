import redis
from redis import Redis
import pymongo
import secrets
import string
import os
import urllib
import json
import logging
import app.db.redis as redis
import app.db.mongo as mongo

from app.models.keys import UserKey, APIKey

logger = logging.getLogger("app")


class KeyService:
    def __init__(self):
        self.redis_client: Redis = redis.redis_key_client
        self.mongo_client: pymongo.MongoClient = mongo.mongo_client
        self.db = self.mongo_client["gateway"]
        self.key_collection = self.db["apikeys"]
        keyindices = self.key_collection.index_information()
        # Make sure, that key is an index (avoids duplicates);
        if not "key" in keyindices:
            self.key_collection.create_index("key", unique=True)
        self.user_collection = self.db["users"]
        # Make sure, that username is an index (avoids duplicates when creating keys, which automatically adds a user if necessary);
        userindices = self.user_collection.index_information()
        if not "username" in userindices:
            self.user_collection.create_index("username", unique=True)
        self.logger = logger

    def init_keys(self):
        """
        Initialize keys from the database
        """
        activeKeys = {
            x["key"]: json.dumps(UserKey(user=x["user"], key=x["key"]).model_dump())
            for x in self.key_collection.find({"active": True})
        }
        # Clear the current db
        self.redis_client.flushdb()
        # Set up the new one.
        if len(activeKeys) > 0:
            self.redis_client.mset(activeKeys)

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

    def build_new_key_object(self, user: string, key: string, name: string) -> APIKey:
        """
        Function to create a new key object.

        Parameters:
        - key (str): The key value.
        - name (str): The name associated with the key.

        Returns:
        - APIKey: A dictionary representing the key object with "active" status, key, and name.
        """
        return APIKey(user=user, key=key, name=name, active=True)

    def check_key(self, key: string):
        """
        Function to check if a key currently exists

        Parameters:
        - key (str): The key to check.

        Returns:
        - UserKey: A UserKey Object if this key exists, None otherwise
        """
        key_data = self.redis_client.get(key)
        print(key_data)
        print(key)
        if key_data == None:
            return None
        else:
            return UserKey.model_validate(json.loads(key_data))

    def delete_key_for_user(self, key: string, user: string):
        """
        Function to delete an existing key for agiven user. only delete
        the key if it exists for this user.

        Parameters:
        - key (str): The key to check.
        - user (str): The user that requests this deletion

        """
        updated_user = self.user_collection.find_one_and_update(
            {"username": user, "keys": {"$elemMatch": {"$eq": key}}},
            {"$pull": {"keys": key}},
        )
        if not updated_user == None:
            # We found, and updated the user, so we can remove the key
            # removal should be instantaneous
            self.key_collection.update_one({"key": key}, {"$set": {"active": False}})
            self.redis_client.delete(key)

    def delete_key(self, key: string, user: string = None):
        """
        Function to delete an existing key irrespective of who had that key

        Parameters:
        - key (str): The key to check.

        """
        if not user == None:
            updated_user = self.user_collection.find_one_and_update(
                {"keys": {"$elemMatch": {"$eq": key}}, "username": user},
                {"$pull": {"keys": key}},
            )
        else:
            # This should be an admin call.
            updated_user = self.user_collection.find_one_and_update(
                {"keys": {"$elemMatch": {"$eq": key}}},
                {"$pull": {"keys": key}},
            )
        # Since all keys have to be associated with a user...
        if not updated_user == None:
            self.logger.warning("Deleted a key without association to a user")
        # User updated / or not. We will inactivate the key now.
        self.key_collection.update_one({"key": key}, {"$set": {"active": False}})
        # NOTE: We do NOT remove any log files for the key.
        self.redis_client.delete(key)

    def set_key_activity(self, key: string, user: string, active: bool):
        """
        Function to set whether a key is active or not.
        The key has to be owned by the user indicated.

        Parameters:
        - key (str): The key to check.
        - user (str): The user that requests this deletion
        - active (bool): whether to activate or deactivate the key
        """
        user_has_key = self.user_collection.find_one(
            {"username": user, "keys": {"$elemMatch": {"$eq": key}}}
        )
        if not user_has_key == None:
            # the requesting user has access to this key
            self.key_collection.update_one({"key": key}, {"$set": {"active": active}})
            if active:
                self._add_key_to_redis(key, user)
            else:
                self.redis_client.srem("keys", key)

    def _add_key_to_redis(self, key: string, user: string):
        """
        Function to add a key to the redis database.

        Parameters:
        - key (str): The key to add.
        - user (str): The user that requests this addition
        """
        self.redis_client.set(key, json.dumps(UserKey(user=user, key=key).model_dump()))

    def add_key(self, user: string, name: string, api_key: str):
        """
        Adds a key for a specific user if the key doesn't exist yet.

        Args:
        - user: Username of the user to whom the API key will be associated.
        - name: Name or label for the API key.
        - api_key: The key itself

        Returns:
        - bool: true, if the key was added false if not.
        """
        key_created = False
        found = self.key_collection.find_one({"key": api_key})
        if found == None:
            self.key_collection.insert_one(
                self.build_new_key_object(user, api_key, name).model_dump()
            )
            self.user_collection.update_one(
                {"username": user}, {"$addToSet": {"keys": api_key}}, upsert=True
            )
            self._add_key_to_redis(api_key, user)
            key_created = True
        return key_created

    def create_key(self, user: string, name: string):
        """
        Generates a unique API key and associates it with a specified user.

        Args:
        - user: Username of the user to whom the API key will be associated.
        - name: Name or label for the API key.

        Returns:
        - api_key: The generated unique API key associated with the user.
        """
        api_key = ""
        api_key = self.generate_api_key()
        userinfo = self.user_collection.find_one({"username": user})
        if userinfo == None or len(userinfo["keys"]) < 10:
            while not self.add_key(user=user, name=name, api_key=api_key):
                api_key = self.generate_api_key()
            return api_key
        else:
            return None

    def list_keys(self, user=None):
        """
        List the available

        Args:
        - user: Username of the user who requests their keys, None if all keys are requested

        Returns:
        - a list of keys in the format [{'key' : key, 'active' : True/False, 'name' : keyname}]
        """
        if user == None:
            # Return everything
            self.logger.info("Trying to obtain keys")
            keys = [x for x in self.key_collection.find({})]
        else:
            userinfo = self.user_collection.find({"username": user})
            userkeys = userinfo[0]["keys"]
            keys = self.key_collection.find({"key": {"$in": userkeys}})

        return [
            {"key": x["key"], "active": x["active"], "name": x["name"]} for x in keys
        ]

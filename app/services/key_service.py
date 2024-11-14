import redis
import pymongo
from pymongo.errors import DuplicateKeyError
import secrets
import string
import json
from fastapi import HTTPException
import logging
from typing import Union


import app.db.redis
import app.db.mongo

from app.models.keys import APIKey

logger = logging.getLogger("app")


class KeyService:
    def __init__(self):
        self.redis_client: redis.Redis = app.db.redis.redis_key_client
        self.mongo_client: pymongo.MongoClient = app.db.mongo.mongo_client
        self.db = self.mongo_client[app.db.mongo.DB_NAME]
        self.key_collection = self.db[app.db.mongo.KEY_COLLECTION]
        self.user_collection = self.db[app.db.mongo.USER_COLLECTION]
        self.logger = logger

    def init_keys(self):
        """
        Initialize keys from the database, and check that indexing is set up properly.
        """

        keyindices = self.key_collection.index_information()
        # Make sure, that key is an index (avoids duplicates);
        if not "key" in keyindices:
            self.key_collection.create_index("key", unique=True)

        activeKeys = {
            x["key"]: json.dumps(APIKey.model_validate(x).model_dump())
            for x in self.key_collection.find({"active": True}, {"_id": 0})
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

    def _build_new_key_object(
        self, user: string, key: string, name: string, user_key: bool = True
    ) -> APIKey:
        """
        Function to create a new key object.

        Parameters:
        - key (str): The key value.
        - name (str): The name associated with the key.

        Returns:
        - APIKey: A dictionary representing the key object with "active" status, key, and name.
        """
        return APIKey(user=user, key=key, name=name, active=True, user_key=user_key)

    def get_user_key_if_active(self, key: string) -> Union[APIKey, None]:
        """
        Function to check if a key currently exists. This only checks in Redis,
        not in the persitent storage, as those two should be in sync.

        Parameters:
        - key (str): The key to check.

        Returns:
        - UserKey: A UserKey Object if this key exists, None otherwise
        """
        key_data = self.redis_client.get(key)
        if key_data == None:
            return None
        else:
            # There are only active keys in the redis db.
            return APIKey.model_validate(json.loads(key_data))

    def delete_key_for_user(self, key: string, user: string):
        """
        Function to delete an existing key for agiven user. only delete
        the key if it exists for this user.

        Parameters:
        - key (str): The key to check.
        - user (str): The user that requests this deletion

        """
        updated_user = self.user_collection.find_one_and_update(
            {app.db.mongo.ID_FIELD: user, "keys": {"$elemMatch": {"$eq": key}}},
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
                {"keys": {"$elemMatch": {"$eq": key}}, app.db.mongo.ID_FIELD: user},
                {"$pull": {"keys": key}},
            )
        else:
            # This should be an admin call.
            updated_user = self.user_collection.find_one_and_update(
                {"keys": {"$elemMatch": {"$eq": key}}},
                {"$pull": {"keys": key}},
            )
        # Since all keys have to be associated with a user...
        if updated_user == None:
            self.logger.warning("Deleted a key without association to a user")
        # User updated / or not. We will inactivate the key now.
        self.key_collection.update_one({"key": key}, {"$set": {"active": False}})
        # NOTE: We do NOT remove any log files for the key.
        self.redis_client.delete(key)

    def set_key_activity(self, key: APIKey, active: bool):
        """
        Function to set whether a key is active or not.
        The key has to be owned by the user indicated.

        Parameters:
        - key (str): The key to check.
        - active (bool): whether to activate or deactivate the key
        """

        if key.active == active:
            return
        else:
            key.active = active
        self.key_collection.find_one_and_update(
            {"key": key.key},
            {"$set": {"active": active}},
            {"_id": 0},
        )
        if active:
            self._set_key_in_redis(key)
        else:
            self.redis_client.delete(key.key)

    def set_key_activity(self, key: APIKey, active: bool):
        """
        Function to set whether a key is active or not.
        The key has to be owned by the user indicated.

        Parameters:
        - key (str): The key to check.
        - active (bool): whether to activate or deactivate the key
        """

        if key.active == active:
            return
        else:
            key.active = active
        self.key_collection.find_one_and_update(
            {"key": key.key},
            {"$set": {"active": active}},
            {"_id": 0},
        )
        if active:
            self._set_key_in_redis(key)
        else:
            self.redis_client.delete(key.key)

    def _set_key_in_redis(self, key: APIKey):
        """
        Function to add a key to the redis database.

        Parameters:
        - key (str): The key to add.
        - user (str): The user that requests this addition
        """
        if key.active:
            self.redis_client.set(key.key, json.dumps(key.model_dump()))
        else:
            # TODO: Check, if this errors if the key is not present.
            self.redis_client.delete(key.key)

    def _add_key(self, key: APIKey):
        """
        Adds a key for a specific user if the key doesn't exist yet.
        The oindicated user has to exist prior to a call to this function.
        Args:
        - user: Username of the user to whom the API key will be associated.
        - name: Name or label for the API key.
        - api_key: The key itself

        Returns:
        - bool: true, if the key was added false if not.
        """

        userinfo = self.user_collection.find_one({app.db.mongo.ID_FIELD: key.user})
        if key.user_key:
            if userinfo == None:
                raise HTTPException(status_code=400, detail="User does not exist")
            if len(userinfo["keys"]) >= 10:
                raise HTTPException(
                    status_code=400,
                    detail="User has reached the maximum number of keys",
                )
        try:
            # This should error, if the key already exists.
            self._add_key_to_mongo(key)
            self._set_key_in_redis(key)
            return True
        except DuplicateKeyError as e:
            return False

    def _add_key_to_mongo(self, key: APIKey):
        """
        Adds a key to the mongo db.

        Args:
        - user: Username of the user to whom the API key will be associated.
        - name: Name or label for the API key.
        - api_key: The key itself

        Returns:
        - bool: true, if the key was added false if not.
        """
        # This should error, if the key already exists.

        self.key_collection.insert_one(key.model_dump())
        if key.user_key:
            self.user_collection.update_one(
                {app.db.mongo.ID_FIELD: key.user},
                {"$addToSet": {"keys": key.key}},
                upsert=False,
            )

    def create_key(self, user: string, name: string, user_key: bool = True):
        """
        Generates a unique API key and associates it with a specified user.
        The User MUST exist prior to calling this function.
        Args:
        - user: Username of the user to whom the API key will be associated.
        - name: Name or label for the API key.

        Returns:
        - api_key: The generated unique API key associated with the user.
        """
        key = self.generate_api_key()
        api_key: APIKey = self._build_new_key_object(
            user=user, key=key, name=name, user_key=user_key
        )
        while not self._add_key(api_key):
            api_key.key = self.generate_api_key()
        return api_key

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
            self.logger.debug("Trying to obtain keys")
            keys = [x for x in self.key_collection.find({})]
        else:
            userinfo = self.user_collection.find({app.db.mongo.ID_FIELD: user})
            userkeys = userinfo[0]["keys"]
            keys = self.key_collection.find({"key": {"$in": userkeys}})

        return [
            {"key": x["key"], "active": x["active"], "name": x["name"]} for x in keys
        ]

    def _update_key(self, key: APIKey):
        """
        Function to update a key in the database.
        """
        self.key_collection.update_one({"key": key.key}, {"$set": key.model_dump()})
        self._set_key_in_redis(key)

    def set_key_quota(self, key: str, day_quota: int, week_quota: int):
        """
        Function to set the quota for a key.

        Parameters:
        - key (str): The key to set the quota for.
        - day_quota (int): The daily quota for the key.
        - week_quota (int): The weekly quota for the key.
        """
        api_key = APIKey.model_validate(
            self.key_collection.find_one({"key": key}, {"_id": 0})
        )
        api_key.day_quota = day_quota
        api_key.week_quota = week_quota
        api_key.has_quota = True
        self._update_key(api_key)

    def set_user_key(self, key: str, is_user_key: str):
        """
        Function to set the quota for a key.

        Parameters:
        - key (str): The key to set the quota for.
        - is_user_key (bool): Whether the key is a user key.
        """
        api_key = APIKey.model_validate(
            self.key_collection.find_one({"key": key}, {"_id": 0})
        )
        api_key.user_key = is_user_key
        self._update_key(api_key)

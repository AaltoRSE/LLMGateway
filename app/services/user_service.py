""" This module provides User service functionality """

from typing import List
import app.db.mongo as mongo
from app.models.user import User
from pymongo import MongoClient
import logging

logger = logging.getLogger("app")


class UserService:
    """Service for User related business logic"""

    def __init__(self) -> None:
        self.mongo_client: MongoClient = mongo.mongo_client
        self.db = self.mongo_client["gateway"]
        self.user_collection = self.db[mongo.USER_COLLECTION]
        self.key_collection = self.db[mongo.KEY_COLLECTION]

    def init_user_db(self):
        # Make sure, that username is an index (avoids duplicates when creating keys, which automatically adds a user if necessary);
        userindices = self.user_collection.index_information()
        if not mongo.ID_FIELD in userindices:
            self.user_collection.create_index(mongo.ID_FIELD, unique=True)

    def get_user_by_id(self, user_id: int) -> User:
        user = self.user_collection.find_one({mongo.ID_FIELD: user_id})
        if not user:
            return None
        return User.model_validate(user)

    def get_or_create_user_from_auth_data(
        self, auth_id: str, first_name: str, last_name: str, email: str = ""
    ) -> User:
        user = self.get_user_by_id(auth_id)
        if not user:

            user = self.create_new_user(
                User(
                    auth_id=auth_id,
                    first_name=first_name,
                    last_name=last_name,
                    admin=False,
                    seen_guide_version="",
                    email=email,
                )
            )
        return user

    def get_all_users(self) -> List[User]:
        users = [User.model_validate(user) for user in self.user_collection.find({})]
        return users

    def reset_user(self, username: User):
        user = self.user_collection.find_one({"auth_id": username})
        logger.info(f"Resetting user {username}")
        logger.info(user)
        user["seen_guide_version"] = ""
        user["keys"] = [
            entry["key"]
            for entry in self.key_collection.find(
                {"user": username, "active": True}, {"key": 1}
            )
        ]
        logger.info(user)
        result = self.user_collection.find_one_and_update(
            {"auth_id": username}, {"$set": user}, upsert=False, projection={"_id": 0}
        )
        logger.info(result)
        return result

    def create_new_user(self, user: User) -> User:
        try:
            new_user = self.user_collection.insert_one(user.model_dump())
            print(new_user)
            return user
        except Exception as e:
            print(e)
            # TODO: Proper handling here.
            return None

    def delete_user(self, user_id: int):
        self.user_collection.delete_one({"auth_id": user_id})

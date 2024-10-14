""" This module provides User service functionality """

from typing import List
import app.db.mongo as mongo
from app.models.user import User
from pymongo import MongoClient
from pymongo import ReturnDocument as Document
import logging
from fastapi import HTTPException
import os

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

    def update_agreement_version(self, username: str, version: str):
        result = self.user_collection.find_one_and_update(
            {mongo.ID_FIELD: username},
            {"$set": {"seen_guide_version": version}},
            upsert=False,
        )
        if not result:
            raise HTTPException(status_code=400, detail="User not found")

    def reset_user(self, user: User):
        db_user = self.user_collection.find_one({mongo.ID_FIELD: user.auth_id})
        if not db_user:
            raise HTTPException(status_code=400, detail="User not found")
        logger.info(f"Resetting user {user.auth_id}")
        logger.info(user)
        db_user["seen_guide_version"] = ""
        db_user["keys"] = [
            entry["key"]
            for entry in self.key_collection.find(
                {"user": user.auth_id, "active": True}, {"key": 1}
            )
        ]
        logger.info(db_user)
        result = self.user_collection.find_one_and_update(
            {mongo.ID_FIELD: db_user["auth_id"]},
            {"$set": db_user},
            upsert=False,
            projection={"_id": 0},
            return_document=Document.AFTER,
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

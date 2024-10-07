import logging

logger = logging.getLogger("app")
import pymongo
from datetime import datetime
from pymongo.database import Database
from pymongo.collection import Collection
from app.models.quota import QuotaElements, UsagePerKeyForUser, KeyPerModelUsage
from app.services.quota_service import get_usage_from_mongo_for_target
from typing import List
import app.db.mongo as mongo_db

# This class handle interaction with the usage databases.
# There are three databases one per-key and one per user usage as in memory redis databases
# a third database actually persistantly stores the quota on a per key basis
# When quota is updated, the current quota per user and key need to be updated
# atomically in redis. In addition, a new entry in the persistent quota database needs to be made.
# Quota has three parts:
#


class UsageService:
    def __init__(self):
        self.mongo_client: pymongo.MongoClient = mongo_db.mongo_client
        self.db: Database = self.mongo_client["gateway"]
        self.usage_collection: Collection = self.db[mongo_db.QUOTA_COLLECTION]
        self.user_collection: Collection = self.db[mongo_db.USER_COLLECTION]
        self.key_collection: Collection = self.db[mongo_db.KEY_COLLECTION]

    def get_usage_per_model(
        self,
        field: str = None,
        target: str = None,
        from_time: datetime = None,
        to_time: datetime = None,
    ) -> List[QuotaElements]:
        query = {}
        timestamp_query = {}
        if to_time is not None:
            timestamp_query["$lte"] = to_time
        if from_time is not None:
            timestamp_query["$gte"] = from_time
        if timestamp_query:
            query["timestamp"] = timestamp_query

        if field is not None:
            if target is None:
                raise ValueError("If field is set, target must be set")
            query[field] = target

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$model",
                    "cost": {"$sum": "$cost"},
                    "prompt_tokens": {"$sum": "$prompt_tokens"},
                    "completion_tokens": {"$sum": "$completion_tokens"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "model": "$_id",
                    "cost": 1,
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": {"$add": ["$prompt_tokens", "$completion_tokens"]},
                }
            },
        ]
        data = [
            QuotaElements(model_usage)
            for model_usage in self.usage_collection.aggregate(pipeline)
        ]
        return data

    def get_usage_for_user_per_model(
        self, user: str, from_time: datetime, to_time: datetime
    ):
        return self.get_usage_per_model("user", user, from_time, to_time)

    def get_usage_for_key_per_model(
        self, key: str, from_time: datetime, to_time: datetime
    ):
        return self.get_usage_per_model("key", key, from_time, to_time)

    def get_usage_for_model(
        self,
        model: str,
        from_time: datetime = datetime.fromtimestamp(0),
        to_time: datetime = None,
    ):
        return get_usage_from_mongo_for_target(
            usage_collection=self.usage_collection,
            target="model",
            key=model,
            from_time=from_time,
            to_time=to_time,
        )

    def get_usage_for_user(
        self,
        user: str,
        from_time: datetime = datetime.fromtimestamp(0),
        to_time: datetime = None,
    ):
        return get_usage_from_mongo_for_target(
            usage_collection=self.usage_collection,
            target="user",
            key=user,
            from_time=from_time,
            to_time=to_time,
        )

    def get_usage_for_key(
        self,
        key: str,
        from_time: datetime = datetime.fromtimestamp(0),
        to_time: datetime = None,
    ):
        return get_usage_from_mongo_for_target(
            usage_collection=self.usage_collection,
            target="key",
            key=key,
            from_time=from_time,
            to_time=to_time,
        )

    def get_usage_per_key_for_user(
        self,
        user: str,
        from_time: datetime = None,
        to_time: datetime = None,
        only_active: bool = False,
    ) -> UsagePerKeyForUser:
        query = {"user": user}
        timestamp_query = {}
        if to_time is not None:
            timestamp_query["$lte"] = to_time
        if from_time is not None:
            timestamp_query["$gte"] = from_time
        if timestamp_query:
            query["timestamp"] = timestamp_query
        pipeline = [
            {"$match": query},
        ]
        if only_active:
            pipeline.extend(
                [
                    {
                        "$lookup": {
                            "from": "apikeys",
                            "localField": "key",
                            "foreignField": "key",
                            "as": "apikey_info",
                        }
                    },
                    {"$unwind": "$apikey_info"},
                    {"$match": {"apikey_info.active": True}},
                ]
            )

        group_pipeline = [
            {
                "$group": {
                    "_id": {"key": "$key", "model": "$model"},
                    "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                    "total_completion_tokens": {"$sum": "$completion_tokens"},
                    "total_cost": {"$sum": "$cost"},
                }
            },
            {
                "$lookup": {
                    "from": "apikeys",
                    "localField": "_id.key",
                    "foreignField": "key",
                    "as": "apikey_info",
                }
            },
            {
                "$group": {
                    "_id": {"key": "$_id.key", "name": {"$first": "$apikey_info.name"}},
                    "models": {
                        "$push": {
                            "model": "$_id.model",
                            "usage": {
                                "prompt_tokens": "$total_prompt_tokens",
                                "completion_tokens": "$total_completion_tokens",
                                "cost": "$total_cost",
                            },
                        }
                    },
                    "total_prompt_tokens": {"$sum": "$total_prompt_tokens"},
                    "total_completion_tokens": {"$sum": "$total_completion_tokens"},
                    "total_cost": {"$sum": "$total_cost"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "key": "$_id.key",
                    "prompt_tokens": "$total_prompt_tokens",
                    "completion_tokens": "$total_completion_tokens",
                    "cost": "$total_cost",
                    "usage": "$models",
                    "name": "$_id.name",
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                    "total_completion_tokens": {"$sum": "$completion_tokens"},
                    "total_cost": {"$sum": "$cost"},
                    "keys": {
                        "$push": {
                            "key": "$key",
                            "prompt_tokens": "$prompt_tokens",
                            "completion_tokens": "$completion_tokens",
                            "cost": "$cost",
                            "usage": "$usage",
                            "name": "$name",
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "prompt_tokens": "$total_prompt_tokens",
                    "completion_tokens": "$total_completion_tokens",
                    "cost": "$total_cost",
                    "keys": "$keys",
                }
            },
        ]

        pipeline.extend(group_pipeline)
        results = list(self.usage_collection.aggregate(pipeline))
        logger.info(results)
        if len(results) == 0:
            usage_data = UsagePerKeyForUser()
            checked_keys = []
        else:
            usage_data = UsagePerKeyForUser.model_validate(results[0])
            checked_keys = [key.key for key in usage_data.keys]
        # Get all keys, and their names from the user and key collections
        key_query = {"user": user}
        if only_active:
            key_query["active"] = True
        all_keys = list(self.key_collection.find(key_query, {"key": 1, "name": 1}))
        unchecked_keys = [
            element for element in all_keys if element["key"] not in checked_keys
        ]
        for key in unchecked_keys:
            usage_data.keys.append(
                KeyPerModelUsage.model_validate(
                    {
                        "key": key["key"],
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cost": 0,
                        "name": key["name"],
                        "usage": [],
                    }
                )
            )
        return usage_data
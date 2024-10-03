import redis
import pymongo
from datetime import datetime
from pymongo.database import Database
from pymongo.collection import Collection
from app.models.quota import (
    QuotaElements,
)
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


class UsageProvider:
    def __init__(self):
        self.mongo_client: pymongo.MongoClient = mongo_db.mongo_client
        self.db: Database = self.mongo_client["gateway"]
        self.usage_collection: Collection = self.db["usage"]

    def get_usage_per_model(
        self,
        field: str = None,
        target: str = None,
        from_time: datetime = None,
        to_time: datetime = None,
    ) -> List[QuotaElements]:
        if to_time is None:
            to_time = datetime.now()
        if from_time is None:
            from_time = datetime.fromtimestamp(0)
        query = {"timestamp": {"$gte": from_time, "$lt": to_time}}
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

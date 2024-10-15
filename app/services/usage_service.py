import logging

logger = logging.getLogger("app")
import pymongo
from datetime import datetime
from pymongo.database import Database
from pymongo.collection import Collection
from app.models.quota import (
    QuotaElements,
    UsagePerKeyForUser,
    KeyPerModelUsage,
    ModelUsage,
    UsageInfo,
)
from app.services.quota_service import get_usage_from_mongo_for_target
from typing import List
import app.db.mongo

# This class handle interaction with the usage databases.
# There are three databases one per-key and one per user usage as in memory redis databases
# a third database actually persistantly stores the quota on a per key basis
# When quota is updated, the current quota per user and key need to be updated
# atomically in redis. In addition, a new entry in the persistent quota database needs to be made.
# Quota has three parts:
#


class UsageService:
    def __init__(self):
        self.mongo_client: pymongo.MongoClient = app.db.mongo.mongo_client
        self.db: Database = self.mongo_client[app.db.mongo.DB_NAME]
        self.usage_collection: Collection = self.db[app.db.mongo.QUOTA_COLLECTION]
        self.user_collection: Collection = self.db[app.db.mongo.USER_COLLECTION]
        self.key_collection: Collection = self.db[app.db.mongo.KEY_COLLECTION]

    def get_usage_per_model(
        self,
        field: str = None,
        target: str = None,
        from_time: datetime = None,
        to_time: datetime = None,
    ) -> List[ModelUsage]:
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
                    "usage": {
                        "cost": "$cost",
                        "prompt_tokens": "$prompt_tokens",
                        "completion_tokens": "$completion_tokens",
                    },
                }
            },
        ]

        model_data = [
            model_usage for model_usage in self.usage_collection.aggregate(pipeline)
        ]
        data = [ModelUsage.model_validate(model_usage) for model_usage in model_data]
        print(data)
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

        # Group to the level of keys.
        group_to_keys_pipeline = [
            {
                "$group": {
                    "_id": {"key": "$key", "model": "$model"},
                    "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                    "total_completion_tokens": {"$sum": "$completion_tokens"},
                    "total_cost": {"$sum": "$cost"},
                }
            },
            {
                "$group": {
                    "_id": {"key": "$_id.key"},
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
                }
            },
            # At this point, we have like max 10 keys, because they are grouped.
            # So we have a minimal number of lookups
            {
                "$lookup": {
                    "from": app.db.mongo.KEY_COLLECTION,
                    "localField": "key",
                    "foreignField": "key",
                    "as": "apikey_info",
                }
            },
        ]

        pipeline.extend(group_to_keys_pipeline)
        # Restrict to active if necessary this should be only max 10 lookups
        if only_active:
            pipeline.append({"$match": {"apikey_info.active": True}})

        # Group to the level of the user.
        group_to_user = [
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
                            "name": {"$first": "$apikey_info.name"},
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
        pipeline.extend(group_to_user)
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

    def get_usage_per_time(self, query: dict, from_time: datetime, to_time: datetime):
        query["timestamp"] = {"$gte": from_time, "$lte": to_time}
        pipeline = self._get_usage_aggregation_pipeline_per_hour(query)
        results = list(self.usage_collection.aggregate(pipeline))
        return results

    def _get_usage_aggregation_pipeline_per_hour(self, query):

        pipeline = [
            query,
            {
                "$addFields": {
                    "hour": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:00:00",
                            "date": "$timestamp",
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$hour",
                    "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                    "total_completion_tokens": {"$sum": "$completion_tokens"},
                    "total_cost": {"$sum": "$cost"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "timestamp": {
                        "$toLong": {"$dateFromString": {"dateString": "$_id"}}
                    },
                    "total_prompt_tokens": 1,
                    "total_completion_tokens": 1,
                    "total_cost": 1,
                }
            },
        ]
        return pipeline

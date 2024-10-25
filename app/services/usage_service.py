import logging

logger = logging.getLogger("app")
import pymongo
from datetime import datetime, timedelta
from pymongo.database import Database
from pymongo.collection import Collection
from app.models.quota import (
    UsageElements,
    UsagePerKeyForUser,
    KeyPerModelUsage,
    ModelUsage,
    PerHourUsage,
    PerUserUsage,
    PerModelUsage,
    UsageElements,
    DEFAULT_USAGE,
    RequestUsage,
    PersistentUsage,
)
from app.models.keys import APIKey
from typing import List
import app.db.mongo


def get_usage_from_mongo_for_target(
    usage_collection: Collection,
    target: str,
    key: str,
    from_time: datetime,
    model: str = None,
    to_time: datetime = None,
) -> UsageElements:
    if to_time is None:
        to_time = datetime.now()
    if from_time is None:
        from_time = datetime.fromtimestamp(0)
    query = {target: key, "timestamp": {"$gte": from_time, "$lt": to_time}}
    if model is not None:
        query["model"] = model
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": "sum",
                "cost": {"$sum": "$cost"},
                "prompt_tokens": {"$sum": "$prompt_tokens"},
                "completion_tokens": {"$sum": "$completion_tokens"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "cost": 1,
                "prompt_tokens": 1,
                "completion_tokens": 1,
            }
        },
    ]
    user_data = list(usage_collection.aggregate(pipeline))

    if len(user_data) == 0:
        return DEFAULT_USAGE
    else:
        user_data = user_data[0]
    return UsageElements(
        prompt_tokens=user_data["prompt_tokens"],
        total_tokens=user_data["prompt_tokens"] + user_data["completion_tokens"],
        completion_tokens=user_data["completion_tokens"],
        cost=user_data["cost"],
    )


# This class handles the interaction with the persistent usage database.
# It is both responsible for adding and retireving information from the database.
# No other class should directly interact with the usage database, and all
# requests to and from it should go through this class.


class UsageService:
    def __init__(self):
        self.mongo_client: pymongo.MongoClient = app.db.mongo.mongo_client
        self.db: Database = self.mongo_client[app.db.mongo.DB_NAME]
        self.usage_collection: Collection = self.db[app.db.mongo.QUOTA_COLLECTION]
        self.user_collection: Collection = self.db[app.db.mongo.USER_COLLECTION]
        self.key_collection: Collection = self.db[app.db.mongo.KEY_COLLECTION]

    def add_persistent_usage(self, model: str, key: APIKey, request: RequestUsage):
        # Update the persistent quota
        cost = (
            request.completion_cost * request.completion_tokens
            + request.prompt_cost * request.prompt_tokens
        )

        quota = PersistentUsage(
            key=key.key,
            model=model,
            prompt_tokens=request.prompt_tokens,
            completion_tokens=request.completion_tokens,
            cost=cost,
            timestamp=datetime.now(),
        )
        if key.user_key:
            quota.user = key.user
        self.usage_collection.insert_one(quota.model_dump())

    def get_user_quota_from_mongo(
        self,
        user: str,
        from_time: datetime,
        model: str = None,
        to_time: datetime = None,
    ) -> UsageElements:
        return get_usage_from_mongo_for_target(
            usage_collection=self.usage_collection,
            target="user",
            key=user,
            from_time=from_time,
            model=model,
            to_time=to_time,
        )

    def get_key_quota_from_mongo(
        self,
        key: str,
        from_time: datetime,
        model: str = None,
        to_time: datetime = None,
    ) -> UsageElements:
        return get_usage_from_mongo_for_target(
            usage_collection=self.usage_collection,
            target="key",
            key=key,
            from_time=from_time,
            model=model,
            to_time=to_time,
        )

    def _get_usage_per_model(
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
        return self._get_usage_per_model("user", user, from_time, to_time)

    def get_usage_for_key_per_model(
        self, key: str, from_time: datetime, to_time: datetime
    ):
        return self._get_usage_per_model("key", key, from_time, to_time)

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

    def get_usage_per_time(
        self, query: dict, from_time: datetime = None, to_time: datetime = None
    ):
        if not from_time:
            from_time = datetime.fromtimestamp(0)
        if not to_time:
            to_time = datetime.now()
        query["timestamp"] = {"$gte": from_time, "$lte": to_time}
        pipeline = self._get_usage_aggregation_pipeline_per_hour(query)
        results = list(self.usage_collection.aggregate(pipeline))
        return [PerHourUsage.model_validate(entry) for entry in results]

    def _get_usage_aggregation_pipeline_per_hour(self, query):

        pipeline = [
            {"$match": query},
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
                    "prompt_tokens": {"$sum": "$prompt_tokens"},
                    "completion_tokens": {"$sum": "$completion_tokens"},
                    "cost": {"$sum": "$cost"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "timestamp": "$_id",
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "cost": 1,
                }
            },
        ]
        return pipeline

    def get_usage_per_user(self):
        one_week_ago = datetime.now() - timedelta(weeks=1)
        # Aggregation pipeline
        pipeline = [
            {
                "$group": {
                    "_id": "$user",
                    "total_cost": {"$sum": "$cost"},
                    "last_week_cost": {
                        "$sum": {
                            "$cond": [
                                {"$gte": ["$timestamp", one_week_ago]},
                                "$cost",
                                0,
                            ]
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "user": "$_id",
                    "total_cost": 1,
                    "last_week_cost": 1,
                }
            },
        ]

        # Execute the aggregation

        result = list(self.usage_collection.aggregate(pipeline))
        return {
            "last_week": {user["user"]: user["last_week_cost"] for user in result},
            "total": {user["user"]: user["total_cost"] for user in result},
        }

    def get_usage_over_time_for_user(self, user: str) -> List[PerHourUsage]:
        query = {"user": user}
        return sorted(self.get_usage_per_time(query), key=lambda x: x.timestamp)

    def get_usage_over_time_for_model(self, model: str) -> List[PerHourUsage]:
        query = {"model": model}
        return sorted(self.get_usage_per_time(query), key=lambda x: x.timestamp)

    def get_usage_per_model_per_hour(self) -> List[PerModelUsage]:
        pipeline = self._per_element_per_hour_usage_pipeline("model")
        result = [
            PerModelUsage.model_validate(entry)
            for entry in (self.usage_collection.aggregate(pipeline))
        ]
        return result

    def get_usage_per_user_per_hour(self) -> List[PerUserUsage]:
        pipeline = self._per_element_per_hour_usage_pipeline("user")
        result = [
            PerUserUsage.model_validate(entry)
            for entry in (self.usage_collection.aggregate(pipeline))
        ]
        return result

    def _per_element_per_hour_usage_pipeline(self, target_element):
        pipeline = [
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
                    "_id": {
                        f"{target_element}": f"${target_element}",
                        "timestamp": "$hour",
                    },
                    "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                    "total_completion_tokens": {"$sum": "$completion_tokens"},
                    "total_cost": {"$sum": "$cost"},
                }
            },
            {
                "$group": {
                    "_id": f"$_id.{target_element}",
                    "usage": {
                        "$push": {
                            "timestamp": "$_id.timestamp",
                            "prompt_tokens": "$total_prompt_tokens",
                            "completion_tokens": "$total_completion_tokens",
                            "cost": "$total_cost",
                        }
                    },
                    "total_cost": {"$sum": "$total_cost"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    f"{target_element}": "$_id",
                    "usage": 1,
                    "cost": "$total_cost",
                }
            },
        ]
        return pipeline

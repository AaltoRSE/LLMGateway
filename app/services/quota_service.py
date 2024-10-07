import redis
import pymongo
import json
import logging

logger = logging.getLogger("app")

from datetime import datetime
from pymongo.database import Database
from pymongo.collection import Collection
from app.models.quota import (
    Quota,
    UserQuota,
    KeyQuota,
    ElementQuota,
    RequestQuota,
    PersistentQuota,
    QuotaElements,
    DEFAULT_USAGE,
)
from app.models.keys import UserKey
from typing import List
import app.db.redis as redis_db
import app.db.mongo as mongo_db

# This class handle interaction with the usage databases.
# There are three databases one per-key and one per user usage as in memory redis databases
# a third database actually persistantly stores the quota on a per key basis
# When quota is updated, the current quota per user and key need to be updated
# atomically in redis. In addition, a new entry in the persistent quota database needs to be made.
# Quota has three parts:
#


def update_key_atomic(
    client: redis.Redis,
    key: str,
    update_function: callable,
    retrieval_function: callable,
    dump_function: callable,
):
    while True:
        try:
            client.watch(key)  # Watch the key for changes

            # Read the current model from Redis
            model_dump = client.get(key)

            model = retrieval_function(model_dump)

            # Modify the model
            update_function(model)

            # Start the transaction
            p = client.pipeline()

            # Write the updated model back to Redis
            p.set(key, dump_function(model))

            # Execute the transaction
            p.execute()
            break  # Break the loop if successful

        except redis.WatchError:
            # If the key was changed by another process, retry
            continue


def get_usage_from_mongo_for_target(
    usage_collection: Collection,
    target: str,
    key: str,
    from_time: datetime,
    model: str = None,
    to_time: datetime = None,
) -> QuotaElements:
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
    return QuotaElements(
        prompt_tokens=user_data["prompt_tokens"],
        total_tokens=user_data["prompt_tokens"] + user_data["completion_tokens"],
        completion_tokens=user_data["completion_tokens"],
        cost=user_data["cost"],
    )


class QuotaService:
    def __init__(self):
        self.user_db = redis_db.redis_usage_user_client
        self.key_db = redis_db.redis_usage_key_client
        self.mongo_client: pymongo.MongoClient = mongo_db.mongo_client
        self.db: Database = self.mongo_client["gateway"]
        self.usage_collection: Collection = self.db[mongo_db.QUOTA_COLLECTION]

    def get_quota(self, key, user) -> Quota:
        return Quota(
            user_quota=self.get_user_quota(user),
            key_quota=self.get_key_quota(key),
        )

    def check_quota(self, requester: UserKey):
        self.get_quota(requester.key, requester.user).check_quota()

    def get_key_quota(self, key: str, from_timestamp: datetime = None) -> KeyQuota:
        keyQuotaData = self.key_db.get(key)
        if keyQuotaData is None:
            return self.get_key_quota_from_mongo(key, from_time=from_timestamp)
        return self.process_key_dump(keyQuotaData)

    def get_user_quota(self, user: str, from_timestamp: datetime = None) -> UserQuota:
        userQuotaData = self.user_db.get(user)
        if userQuotaData is None:
            return self.get_user_quota_from_mongo(user, from_time=from_timestamp)
        return self.process_user_dump(userQuotaData)

    def process_key_dump(self, dump: str):
        if dump is None:
            # Check, if there is quota data in the persitent database
            keyQuota = KeyQuota()
        else:
            keyQuota = KeyQuota.model_validate(json.loads(dump))
        return keyQuota

    def update_persistent_quota(
        self, model: str, key: str, user: str, request: RequestQuota
    ):
        # Update the persistent quota
        cost = (
            request.completion_cost * request.completion_tokens
            + request.prompt_cost * request.prompt_tokens
        )
        quota = PersistentQuota(
            key=key,
            user=user,
            model=model,
            prompt_tokens=request.prompt_tokens,
            completion_tokens=request.completion_tokens,
            cost=cost,
            timestamp=datetime.now(),
        )
        self.usage_collection.insert_one(quota.model_dump())

    def get_user_quota_from_mongo(
        self,
        user: str,
        from_time: datetime,
        model: str = None,
        to_time: datetime = None,
    ) -> UserQuota:
        return UserQuota(
            usage=get_usage_from_mongo_for_target(
                usage_collection=self.usage_collection,
                target="user",
                key=user,
                from_time=from_time,
                model=model,
                to_time=to_time,
            )
        )

    def get_key_quota_from_mongo(
        self,
        key: str,
        from_time: datetime,
        model: str = None,
        to_time: datetime = None,
    ) -> KeyQuota:
        return KeyQuota(
            usage=get_usage_from_mongo_for_target(
                usage_collection=self.usage_collection,
                target="key",
                key=key,
                from_time=from_time,
                model=model,
                to_time=to_time,
            )
        )

    def process_user_dump(self, dump: str):
        if dump is None:
            userQuota = UserQuota()
        else:
            userQuota = UserQuota.model_validate(json.loads(dump))
        return userQuota

    def update_key_quota(self, key: str, request: RequestQuota):
        update_key_atomic(
            client=self.key_db,
            key=key,
            retrieval_function=lambda data: self.process_key_dump(data),
            update_function=lambda model: model.add_request(request),
            dump_function=lambda model: json.dumps(model.model_dump()),
        )

    def update_user_quota(self, user: str, request: RequestQuota):
        update_key_atomic(
            client=self.key_db,
            key=user,
            retrieval_function=lambda data: self.process_user_dump(data),
            update_function=lambda model: model.add_request(request),
            dump_function=lambda model: json.dumps(model.model_dump()),
        )

    def update_quota(self, source: UserKey, model: str, request: RequestQuota):
        self.update_key_quota(key=source.key, request=request)
        self.update_user_quota(user=source.user, request=request)
        self.update_persistent_quota(
            key=source.key, user=source.user, model=model, request=request
        )

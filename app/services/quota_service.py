import redis
import json
import logging
from typing import Annotated
from fastapi import Depends

logger = logging.getLogger("app")

from datetime import datetime, timedelta

from app.models.quota import (
    Quota,
    UserQuota,
    KeyQuota,
    RequestUsage,
    PersistentUsage,
    TimedKeyQuota,
    TimedQuota,
    TimedUserQuota,
    UserAndKeyQuota,
)
from app.services.usage_service import UsageService
from app.models.keys import APIKey
import app.db.redis as redis_db

# This class handle interaction with the Quota redis clients, and interacts with the UsageService for
# retrieval and updates to the persistent usage storage.
#


def update_key_atomic(
    client: redis.Redis,
    key: str,
    update_function: callable,
    retrieval_function: callable,
    dump_function: callable,
    ttl: int,
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
            p.setex(name=key, time=ttl, value=dump_function(model))

            # Execute the transaction
            p.execute()
            break  # Break the loop if successful

        except redis.WatchError:
            # If the key was changed by another process, retry
            continue


class QuotaService:
    def __init__(self, usage_service: Annotated[UsageService, Depends(UsageService)]):
        self.user_week_db: redis.StrictRedis = redis_db.redis_user_quota_week_client
        self.key_week_db: redis.StrictRedis = redis_db.redis_key_quota_week_client
        self.user_day_db: redis.StrictRedis = redis_db.redis_user_quota_day_client
        self.key_day_db: redis.StrictRedis = redis_db.redis_user_quota_day_client
        self.usage_service: UsageService = usage_service

    def init_quota(self):
        # Cleanup, in case of changes.
        self.user_week_db.flushdb()
        self.key_week_db.flushdb()
        self.user_day_db.flushdb()
        self.key_day_db.flushdb()

    def get_quota(self, key: APIKey) -> Quota:
        key_quota = self.get_key_quotas(
            key=key.key,
            key_has_quota=key.has_quota,
            day_quota=key.day_quota,
            week_quota=key.week_quota,
        )
        if key.user_key:
            user_quota = self.get_user_quotas(key.user)
            return UserAndKeyQuota(user_quota=user_quota, key_quota=key_quota)
        return key_quota

    def check_quota(self, requester: APIKey):
        self.get_quota(requester).check_quota()

    def get_key_quotas(
        self, key: str, key_has_quota=False, day_quota=0, week_quota=0
    ) -> TimedKeyQuota:
        start_week = self.getStartOfWeekDate()
        start_day = self.getStartOfDayDate()
        key_week_quota = self._get_key_quota_from_redis(
            self.key_week_db, key, from_timestamp=start_week
        )
        key_day_quota = self._get_key_quota_from_redis(
            self.key_day_db, key, from_timestamp=start_day
        )
        if key_has_quota:
            key_week_quota.quota.cost = week_quota
            key_day_quota.quota = day_quota
        return TimedKeyQuota(week_quota=key_week_quota, day_quota=key_day_quota)

    def get_user_quotas(self, user: str) -> TimedUserQuota:
        start_week = self.getStartOfWeekDate()
        start_day = self.getStartOfDayDate()
        user_week_quota = self._get_user_quota_from_redis(
            self.user_week_db, user, from_timestamp=start_week
        )
        user_day_quota = self._get_user_quota_from_redis(
            self.user_day_db, user, from_timestamp=start_day
        )
        return TimedUserQuota(week_quota=user_week_quota, day_quota=user_day_quota)

    def _get_key_quota_from_redis(
        self, redis: redis.StrictRedis, key: str, from_timestamp: datetime = None
    ) -> KeyQuota:
        keyQuotaData = redis.get(key)
        if keyQuotaData is None:
            return KeyQuota(
                usage=self.usage_service.get_key_quota_from_mongo(
                    key, from_time=from_timestamp
                )
            )
        return self.process_key_dump(keyQuotaData)

    def _get_user_quota_from_redis(
        self, redis: redis.StrictRedis, user: str, from_timestamp: datetime = None
    ) -> UserQuota:
        userQuotaData = redis.get(user)
        if userQuotaData is None:
            return UserQuota(
                usage=self.usage_service.get_user_quota_from_mongo(
                    user, from_time=from_timestamp
                )
            )
        return self.process_user_dump(userQuotaData)

    def process_key_dump(self, dump: str):
        if dump is None:
            # Check, if there is quota data in the persitent database
            keyQuota = KeyQuota()
        else:
            keyQuota = KeyQuota.model_validate(json.loads(dump))
        return keyQuota

    def process_user_dump(self, dump: str):
        if dump is None:
            userQuota = UserQuota()
        else:
            userQuota = UserQuota.model_validate(json.loads(dump))
        return userQuota

    def add_key_usage(self, key: str, request: RequestUsage):
        ttl_day = self.getEndOfDaySeconds()
        ttl_week = self.getEndOfWeekSeconds()
        update_key_atomic(
            client=self.key_day_db,
            key=key,
            retrieval_function=lambda data: self.process_key_dump(data),
            update_function=lambda model: model.add_request(request),
            dump_function=lambda model: json.dumps(model.model_dump()),
            ttl=ttl_day,
        )
        update_key_atomic(
            client=self.key_week_db,
            key=key,
            retrieval_function=lambda data: self.process_key_dump(data),
            update_function=lambda model: model.add_request(request),
            dump_function=lambda model: json.dumps(model.model_dump()),
            ttl=ttl_week,
        )

    def getEndOfDaySeconds(self):
        now = datetime.now()
        return 86400 - (now.hour * 3600 + now.minute * 60 + now.second)

    def getEndOfWeekSeconds(self):
        now = datetime.now()
        return 604800 - (
            now.weekday() * 86400 + now.hour * 3600 + now.minute * 60 + now.second
        )

    def getStartOfWeekDate(self):
        now = datetime.now()
        return now - timedelta(
            days=now.weekday(), hours=now.hour, minutes=now.minute, seconds=now.second
        )

    def getStartOfDayDate(self):
        now = datetime.now()
        return now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)

    def add_user_usage(self, user: str, request: RequestUsage):
        ttl_day = self.getEndOfDaySeconds()
        ttl_week = self.getEndOfWeekSeconds()
        update_key_atomic(
            client=self.user_day_db,
            key=user,
            retrieval_function=lambda data: self.process_user_dump(data),
            update_function=lambda model: model.add_request(request),
            dump_function=lambda model: json.dumps(model.model_dump()),
            ttl=ttl_day,
        )
        update_key_atomic(
            client=self.user_day_db,
            key=user,
            retrieval_function=lambda data: self.process_user_dump(data),
            update_function=lambda model: model.add_request(request),
            dump_function=lambda model: json.dumps(model.model_dump()),
            ttl=ttl_week,
        )

    def add_usage(self, source: APIKey, model: str, request: RequestUsage):
        self.usage_service.add_persistent_usage(
            key=source, model=model, request=request
        )
        self.add_key_usage(key=source.key, request=request)
        if source.user_key:
            self.add_user_usage(user=source.user, request=request)

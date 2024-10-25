import os
import redis

REDIS_MODEL_DB = 0
REDIS_KEY_DB = 1
REDIS_KEY_USAGE_DAY_DB = 2
REDIS_KEY_USAGE_WEEK_DB = 3
REDIS_SESSION_DB = 4
REDIS_USER_USAGE_DAY_DB = 5
REDIS_USER_USAGE_WEEK_DB = 6


redis_host = os.environ.get("REDISHOST", "redis")
redis_port = os.environ.get("REDISPORT", "6379")
redis_model_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_MODEL_DB
)

redis_key_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_KEY_DB
)

redis_key_quota_day_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_KEY_USAGE_DAY_DB
)

redis_key_quota_week_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_KEY_USAGE_WEEK_DB
)

redis_session_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_SESSION_DB
)


redis_user_quota_day_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_USER_USAGE_DAY_DB
)

redis_user_quota_week_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_USER_USAGE_WEEK_DB
)

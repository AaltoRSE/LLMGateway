import os
import redis

REDIS_MODEL_DB = 0
REDIS_KEY_DB = 1
REDIS_USER_USAGE_DB = 2
REDIS_KEY_USAGE_DB = 3

redis_host = os.environ.get("REDISHOST", "redis")
redis_port = os.environ.get("REDISPORT", "6379")
redis_model_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_MODEL_DB
)

redis_key_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_KEY_DB
)

redis_usage_key_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_KEY_USAGE_DB
)

redis_usage_user_client = redis.StrictRedis(
    host=redis_host, port=int(redis_port), db=REDIS_USER_USAGE_DB
)

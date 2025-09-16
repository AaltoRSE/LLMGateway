import os
import redis.asyncio as redis

REDIS_MODEL_DB = 0
REDIS_KEY_DB = 1
REDIS_KEY_USAGE_MONTH_DB = 3
REDIS_SESSION_DB = 4
REDIS_USER_USAGE_MONTH_DB = 6
REDIS_USER_BALANCE_DB = 7
REDIS_KEY_BALANCE_DB = 8


redis_host = os.environ.get("REDISHOST", "redis")
redis_port = os.environ.get("REDISPORT", "6379")


async def get_model_client():
    redis_model_client = redis.StrictRedis(
        host=redis_host, port=int(redis_port), db=REDIS_MODEL_DB
    )
    try:
        yield redis_model_client
    finally:
        redis_model_client.close()


async def get_key_client():
    redis_key_client = redis.StrictRedis(
        host=redis_host, port=int(redis_port), db=REDIS_KEY_DB
    )
    try:
        yield redis_key_client
    finally:
        redis_key_client.close()


async def get_key_quota_client():
    redis_key_quota_month_client = redis.StrictRedis(
        host=redis_host, port=int(redis_port), db=REDIS_KEY_USAGE_MONTH_DB
    )
    try:
        yield redis_key_quota_month_client
    finally:
        redis_key_quota_month_client.close()


async def get_session_client():
    redis_session_client = redis.StrictRedis(
        host=redis_host, port=int(redis_port), db=REDIS_SESSION_DB
    )
    try:
        yield redis_session_client
    finally:
        redis_session_client.close()


async def get_user_quota_client():
    redis_user_quota_month_client = redis.StrictRedis(
        host=redis_host, port=int(redis_port), db=REDIS_USER_USAGE_MONTH_DB
    )
    try:
        yield redis_user_quota_month_client
    finally:
        redis_user_quota_month_client.close()


async def get_user_balance_client():
    redis_user_balance_client = redis.StrictRedis(
        host=redis_host, port=int(redis_port), db=REDIS_USER_BALANCE_DB
    )
    try:
        yield redis_user_balance_client
    finally:
        redis_user_balance_client.close()


async def get_key_balance_client():
    redis_key_balance_client = redis.StrictRedis(
        host=redis_host, port=int(redis_port), db=REDIS_KEY_BALANCE_DB
    )
    try:
        yield redis_key_balance_client
    finally:
        redis_key_balance_client.close()

import os
from typing import AsyncGenerator
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
redis_password = os.environ.get("REDISPASSWORD")


def build_redis_client(db: int) -> redis.Redis:
    return redis.StrictRedis(
        host=redis_host,
        port=int(redis_port),
        db=db,
        password=redis_password,
    )


async def get_model_client() -> AsyncGenerator[redis.StrictRedis, None]:
    redis_model_client = build_redis_client(REDIS_MODEL_DB)
    try:
        yield redis_model_client
    finally:
        await redis_model_client.aclose()


async def get_key_client() -> AsyncGenerator[redis.StrictRedis, None]:
    redis_key_client = build_redis_client(REDIS_KEY_DB)
    try:
        yield redis_key_client
    finally:
        await redis_key_client.aclose()


async def get_key_quota_client() -> AsyncGenerator[redis.StrictRedis, None]:
    redis_key_quota_month_client = build_redis_client(REDIS_KEY_USAGE_MONTH_DB)
    try:
        yield redis_key_quota_month_client
    finally:
        await redis_key_quota_month_client.aclose()


async def get_session_client() -> AsyncGenerator[redis.StrictRedis, None]:
    redis_session_client = build_redis_client(REDIS_SESSION_DB)
    try:
        yield redis_session_client
    finally:
        await redis_session_client.aclose()


async def get_user_quota_client() -> AsyncGenerator[redis.StrictRedis, None]:
    redis_user_quota_month_client = build_redis_client(REDIS_USER_USAGE_MONTH_DB)
    try:
        yield redis_user_quota_month_client
    finally:
        await redis_user_quota_month_client.aclose()


async def get_user_balance_client() -> AsyncGenerator[redis.StrictRedis, None]:
    redis_user_balance_client = build_redis_client(REDIS_USER_BALANCE_DB)
    try:
        yield redis_user_balance_client
    finally:
        await redis_user_balance_client.aclose()


async def get_key_balance_client() -> AsyncGenerator[redis.StrictRedis, None]:
    redis_key_balance_client = build_redis_client(REDIS_KEY_BALANCE_DB)
    try:
        yield redis_key_balance_client
    finally:
        await redis_key_balance_client.aclose()

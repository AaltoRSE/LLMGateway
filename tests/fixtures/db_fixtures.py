from typing import Generator
import uuid as uuid

import fakeredis
import pytest

import app.repositories.factories
import app.config.db

from tests.utils.mock_repositories import (
    UserRepositoryImpl,
    LLMModelRepositoryImpl,
    APIKeyRepositoryImpl,
    UsageRepositoryImpl,
    BalanceRepositoryImpl,
)
from tests.utils.repositories import Repositories


@pytest.fixture
def mock_repositories(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Repositories, None, None]:
    """
    Fixture to mock the database connection (working around the dbs).

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Monkeypatch fixture

    Returns
    -------
    MagicMock
        The mocked database connection.
    """
    monkeypatch.setattr(app.config.db, "UserRepositoryImpl", UserRepositoryImpl)
    monkeypatch.setattr(app.config.db, "LLMModelRepositoryImpl", LLMModelRepositoryImpl)
    monkeypatch.setattr(app.config.db, "APIKeyRepositoryImpl", APIKeyRepositoryImpl)
    monkeypatch.setattr(app.config.db, "UsageRepositoryImpl", UsageRepositoryImpl)
    monkeypatch.setattr(app.config.db, "BalanceRepositoryImpl", BalanceRepositoryImpl)
    monkeypatch.setattr(
        app.repositories.factories,
        "get_user_repository_class",
        lambda: UserRepositoryImpl,
    )
    monkeypatch.setattr(
        app.repositories.factories,
        "get_balance_repository_class",
        lambda: BalanceRepositoryImpl,
    )
    monkeypatch.setattr(
        app.repositories.factories,
        "get_llm_repository_class",
        lambda: LLMModelRepositoryImpl,
    )
    monkeypatch.setattr(
        app.repositories.factories,
        "get_usage_repository_class",
        lambda: UsageRepositoryImpl,
    )
    monkeypatch.setattr(
        app.repositories.factories,
        "get_key_repository_class",
        lambda: APIKeyRepositoryImpl,
    )

    user_repo = UserRepositoryImpl()
    model_repo = LLMModelRepositoryImpl()
    key_repo = APIKeyRepositoryImpl()
    usage_repo = UsageRepositoryImpl()
    balance_repo = BalanceRepositoryImpl()
    print("Mocking repositories")
    yield Repositories(
        user_repo=user_repo,
        model_repo=model_repo,
        key_repo=key_repo,
        usage_repo=usage_repo,
        balance_repo=balance_repo,
    )
    user_repo.reset()
    model_repo.reset()
    key_repo.reset()
    usage_repo.reset()
    balance_repo.reset()


# redis_my_proc = factories.redis_proc(port=6379)
# redis_model_client = factories.redisdb("redis_my_proc", 1)
# redis_key_client = factories.redisdb("redis_my_proc", 2)
# redis_key_quota_month_client = factories.redisdb("redis_my_proc", 3)
# redis_session_client = factories.redisdb("redis_my_proc", 4)
# redis_user_quota_month_client = factories.redisdb("redis_my_proc", 5)
# redis_user_balance_client = factories.redisdb("redis_my_proc", 6)
# redis_key_balance_client = factories.redisdb("redis_my_proc", 7)
@pytest.fixture
def redis_model_client():
    redis_client = fakeredis.FakeAsyncRedis()
    #    print(f"Creating Model client: {redis_client}")
    return redis_client


@pytest.fixture
def redis_key_client():
    redis_client = fakeredis.FakeAsyncRedis()
    #    print(f"Creating Key client: {redis_client}")
    return redis_client


@pytest.fixture
def redis_key_quota_month_client():
    redis_client = fakeredis.FakeAsyncRedis()
    #    print(f"Creating Key quota client: {redis_client}")
    return redis_client


@pytest.fixture
def redis_session_client():
    redis_client = fakeredis.FakeAsyncRedis()
    #    print(f"Creating Session client: {redis_client}")
    return redis_client


@pytest.fixture
def redis_user_quota_month_client():
    redis_client = fakeredis.FakeAsyncRedis()
    #    print(f"Creating User Quota client: {redis_client}")
    return redis_client


@pytest.fixture
def redis_user_balance_client():
    redis_client = fakeredis.FakeAsyncRedis()
    #    print(f"Creating user balance client: {redis_client}")
    return redis_client


@pytest.fixture
def redis_key_balance_client():
    redis_client = fakeredis.FakeAsyncRedis()
    #    print(f"Creating key balance client: {redis_client}")
    return redis_client


@pytest.fixture
def redis_dbs(
    monkeypatch,
    redis_model_client,
    redis_key_client,
    redis_key_quota_month_client,
    redis_session_client,
    redis_user_quota_month_client,
    redis_user_balance_client,
    redis_key_balance_client,
):
    print("Redis DBs")
    import app.dbs.redis.redis

    async def patch_model_client():
        yield redis_model_client

    async def patch_key_client():
        yield redis_key_client

    async def patch_key_quota_client():
        yield redis_key_quota_month_client

    async def patch_session_client():
        yield redis_session_client

    async def patch_user_quota_client():
        yield redis_user_quota_month_client

    async def patch_user_balance_client():
        yield redis_user_balance_client

    async def patch_key_balance_client():
        yield redis_key_balance_client

    monkeypatch.setattr(app.dbs.redis.redis, "get_model_client", patch_model_client)

    monkeypatch.setattr(app.dbs.redis.redis, "get_key_client", patch_key_client)
    monkeypatch.setattr(
        app.dbs.redis.redis,
        "get_key_quota_client",
        patch_key_quota_client,
    )
    monkeypatch.setattr(app.dbs.redis.redis, "get_session_client", patch_session_client)
    monkeypatch.setattr(
        app.dbs.redis.redis, "get_user_quota_client", patch_user_quota_client
    )
    monkeypatch.setattr(
        app.dbs.redis.redis, "get_user_balance_client", patch_user_balance_client
    )
    monkeypatch.setattr(
        app.dbs.redis.redis, "get_key_balance_client", patch_key_balance_client
    )

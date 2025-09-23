from typing import AsyncGenerator
import pytest_asyncio
from fastapi import FastAPI

from app.dbs.postgresql.repositories.user_repository import SQLUserRepository
from app.dbs.postgresql.repositories.balance_repository import SQLBalanceRepository
from app.dbs.postgresql.repositories.model_repository import SQLModelRepository
from app.dbs.postgresql.repositories.api_key_repository import SQLAPIKeyRepositry
from app.dbs.postgresql.repositories.usage_repository import SQLUsageRepository
import app.repositories.factories
from app.dbs.redis.redis import (
    get_key_client,
    get_model_client,
    get_user_balance_client,
    get_user_quota_client,
    get_session_client,
    get_key_quota_client,
    get_key_balance_client,
)
import app.dbs.redis.redis

# import app.security.entra_jwt
# from tests.utils.jwt_utils import jwks
from tests.fixtures.db_fixtures import Repositories


@pytest_asyncio.fixture
async def llm_gateway(
    mock_repositories: Repositories, redis_dbs
) -> AsyncGenerator[FastAPI, None]:
    import app.main

    currentapp = app.main.app
    yield currentapp


@pytest_asyncio.fixture
async def setup_repos(
    mock_repositories: Repositories, redis_dbs, llm_gateway: FastAPI
) -> AsyncGenerator[FastAPI, None]:

    # DB overrides
    llm_gateway.dependency_overrides[SQLUserRepository] = (
        app.repositories.factories.get_user_repository_class()
    )
    llm_gateway.dependency_overrides[SQLUsageRepository] = (
        app.repositories.factories.get_usage_repository_class()
    )
    llm_gateway.dependency_overrides[SQLBalanceRepository] = (
        app.repositories.factories.get_balance_repository_class()
    )
    llm_gateway.dependency_overrides[SQLModelRepository] = (
        app.repositories.factories.get_llm_repository_class()
    )
    llm_gateway.dependency_overrides[SQLAPIKeyRepositry] = (
        app.repositories.factories.get_key_repository_class()
    )
    # Redis overrides
    llm_gateway.dependency_overrides[get_model_client] = (
        app.dbs.redis.redis.get_model_client
    )
    llm_gateway.dependency_overrides[get_key_client] = (
        app.dbs.redis.redis.get_key_client
    )
    llm_gateway.dependency_overrides[get_key_quota_client] = (
        app.dbs.redis.redis.get_key_quota_client
    )
    llm_gateway.dependency_overrides[get_session_client] = (
        app.dbs.redis.redis.get_session_client
    )
    llm_gateway.dependency_overrides[get_user_quota_client] = (
        app.dbs.redis.redis.get_user_quota_client
    )
    llm_gateway.dependency_overrides[get_user_balance_client] = (
        app.dbs.redis.redis.get_user_balance_client
    )
    llm_gateway.dependency_overrides[get_key_balance_client] = (
        app.dbs.redis.redis.get_key_balance_client
    )
    yield llm_gateway
    llm_gateway.dependency_overrides = {}


# @pytest.fixture
# def setup_auth(monkeypatch: pytest.MonkeyPatch) -> None:
#    auth_service = app.security.entra_jwt.get_entrajwt_auth_service()
#    auth_service._set_jwks(jwks)  # type: ignore

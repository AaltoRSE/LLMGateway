from typing import AsyncGenerator
import pytest_asyncio

from .db_fixtures import mock_repositories, Repositories

from app.services.key_service import KeyService
from app.services.balance_service import BalanceService
from app.services.usage_service import UsageService
from app.services.model_service import ModelService
from app.services.user_service import UserService
from app.services.session_service import SessionService

from app.dbs.redis.redis import *


@pytest_asyncio.fixture
async def key_service(mock_repositories: Repositories, redis_dbs) -> KeyService:
    service = KeyService(
        key_repository=mock_repositories.key_repo,
        key_db=get_key_client(),
        key_quota_db=get_key_quota_client(),
    )
    return service


@pytest_asyncio.fixture
async def model_service(mock_repositories: Repositories, redis_dbs) -> ModelService:
    service = ModelService(
        llm_repository=mock_repositories.model_repo, model_client=get_model_client()
    )
    return service


@pytest_asyncio.fixture
async def balance_service(mock_repositories: Repositories, redis_dbs) -> BalanceService:
    service = BalanceService(
        apikey_repository=mock_repositories.key_repo,
        balance_repository=mock_repositories.balance_repo,
        user_repository=mock_repositories.user_repo,
        usage_repository=mock_repositories.usage_repo,
        user_balance=get_user_balance_client(),
        key_balance=get_key_balance_client(),
        key_quota=get_key_balance_client(),
        user_quota=get_user_quota_client(),
    )
    return service


@pytest_asyncio.fixture
async def usage_service(mock_repositories: Repositories, redis_dbs) -> UsageService:
    service = UsageService(
        balance_repository=mock_repositories.balance_repo,
        user_repository=mock_repositories.user_repo,
        usage_repository=mock_repositories.usage_repo,
    )
    return service


@pytest_asyncio.fixture
async def user_service(
    mock_repositories: Repositories, redis_dbs, key_service
) -> UserService:
    service = UserService(
        user_repository=mock_repositories.user_repo, key_service=key_service
    )
    return service


@pytest_asyncio.fixture
async def session_service(mock_repositories: Repositories, redis_dbs) -> SessionService:
    service = SessionService(session_client=get_session_client())
    return service

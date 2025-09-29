import pytest_asyncio
from typing import AsyncGenerator
from tests.utils.repositories import Repositories

from app.services.key_service import KeyService
from app.services.balance_service import BalanceService
from app.services.usage_service import UsageService
from app.services.model_service import ModelService
from app.services.user_service import UserService
from app.services.session_service import SessionService


@pytest_asyncio.fixture
async def key_service(
    mock_repositories: Repositories,
    redis_dbs,
    redis_key_client,
    redis_key_quota_month_client,
) -> AsyncGenerator[KeyService, None]:
    print("Setting up key service")
    print(f"db = {redis_key_client}")
    print(f"quota_db = {redis_key_client}")
    service = KeyService(
        key_repository=mock_repositories.key_repo,
        key_db=redis_key_client,
        key_quota_db=redis_key_quota_month_client,
    )
    yield service


@pytest_asyncio.fixture
async def model_service(
    mock_repositories: Repositories, redis_dbs, redis_model_client
) -> AsyncGenerator[ModelService, None]:
    service = ModelService(
        llm_repository=mock_repositories.model_repo,
        model_client=redis_model_client,
    )
    yield service


@pytest_asyncio.fixture
async def balance_service(
    mock_repositories: Repositories,
    redis_dbs,
    redis_user_quota_month_client,
    redis_key_balance_client,
    redis_user_balance_client,
    redis_key_quota_month_client,
) -> AsyncGenerator[BalanceService, None]:
    service = BalanceService(
        apikey_repository=mock_repositories.key_repo,
        balance_repository=mock_repositories.balance_repo,
        user_repository=mock_repositories.user_repo,
        usage_repository=mock_repositories.usage_repo,
    )
    yield service


@pytest_asyncio.fixture
async def usage_service(
    mock_repositories: Repositories, balance_service: BalanceService, redis_dbs
) -> UsageService:
    service = UsageService(
        user_repository=mock_repositories.user_repo,
        usage_repository=mock_repositories.usage_repo,
        key_repository=mock_repositories.key_repo,
        balance_service=balance_service,
    )
    return service


@pytest_asyncio.fixture
async def user_service(
    mock_repositories: Repositories, redis_dbs, key_service
) -> UserService:
    service = UserService(
        user_respository=mock_repositories.user_repo, key_service=key_service
    )
    return service


@pytest_asyncio.fixture
async def session_service(
    mock_repositories: Repositories, redis_dbs, redis_session_client
) -> AsyncGenerator[SessionService, None]:
    service = SessionService(session_client=redis_session_client)
    yield service

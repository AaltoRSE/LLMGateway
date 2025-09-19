import pytest_asyncio

from tests.utils.repositories import Repositories
from tests.fixtures.app_fixtures import setup_repos
from app.dbs.redis.redis import get_key_client, get_key_quota_client
from app.services.user_service import User
from app.services.key_service import KeyService

from .user_fixtures import normal_user


async def create_key(
    mock_repositories: Repositories, for_user: User | None, name: str = "TestKey"
) -> str:
    key_service = KeyService(
        mock_repositories.key_repo, get_key_client(), get_key_quota_client()
    )
    key = await key_service.create_key(
        name, for_user.id if for_user is not None else None
    )
    return key


@pytest_asyncio.fixture
async def user_api_key(mock_repositories, redis_dbs, setup_repos, normal_user):
    key = await create_key(mock_repositories, normal_user)
    return key

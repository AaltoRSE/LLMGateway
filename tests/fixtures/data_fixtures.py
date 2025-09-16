from typing import AsyncGenerator
import pytest_asyncio

from .db_fixtures import mock_repositories, Repositories
from .user_fixtures import normal_user, User
from app.schemas.key_schema import APIKey


@pytest_asyncio.fixture
async def user_key(
    mock_repositories: Repositories, normal_user: User
) -> AsyncGenerator[APIKey, None, None]:
    key = await mock_repositories.key_repo.create_api_key(
        name="UserKey", user_id=normal_user.id
    )
    yield key
    mock_repositories.key_repo.reset()

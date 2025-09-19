"""User Fixtures"""

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from app.schemas.user_schema import User, UserBase
from tests.fixtures.db_fixtures import Repositories


normalData = UserBase(
    auth_id="user",
    first_name="Test",
    last_name="User",
    admin=False,
    accepted_agreement_version="2.0",
    quota="40",
)

adminData = UserBase(
    auth_id="admin",
    first_name="Admin",
    last_name="User",
    admin=True,
    accepted_agreement_version="1.0",
    quota="100",
)


@pytest_asyncio.fixture
async def normal_user(
    mock_repositories: Repositories,
) -> AsyncGenerator[User, None]:
    """
    Fixture to a normal user in the authentication scheme.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Monkeypatch fixture

    """

    user = await mock_repositories.user_repo.create_new_user(normalData)
    yield user
    mock_repositories.usage_repo.reset()


@pytest_asyncio.fixture
async def admin_user(
    mock_repositories: Repositories,
) -> AsyncGenerator[User, None]:
    """
    Fixture to an admin user in the authentication scheme.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Monkeypatch fixture

    """

    user = await mock_repositories.user_repo.create_new_user(adminData)
    yield user
    mock_repositories.usage_repo.reset()


@pytest_asyncio.fixture
async def basic_users(normal_user, admin_user) -> None:
    pass

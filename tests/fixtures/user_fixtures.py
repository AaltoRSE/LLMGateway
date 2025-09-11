"""User Fixtures"""

from typing import Any, Generator
from datetime import datetime
import pytest
from app.security.auth import BackendUser
from app.schemas.user_schema import User
from tests.fixtures.db_fixtures import Repositories
from tests.utils.jwt_utils import create_token_for_user


def get_backend_user(
    user_data: dict[str, Any],
) -> BackendUser:
    user = get_db_user(user_data)
    token = create_token_for_user(user, user_data["data"]["auth_groups"])
    return BackendUser(
        user=user,
        userdata = user_data,
        roles=user_data["data"]["auth_groups"],
        auth_token=token,
        agreement_ok=True
    )


def get_db_user(user_data: dict[str, Any]) -> User:
    return User(
        auth_id=user_data["data"]["auth_name"],
        first_name=user_data["data"]["first_name"],
        last_name=user_data["data"]["last_name"],
        id=user_data["id"],
        admin=user_data["admin"],
        store_data=user_data["store_data"],
        accepted_agreement_version=user_data["agreement"],
        created_at=datetime.strptime(
            "2021-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"
        ).astimezone(),
        last_active=datetime.strptime(
            "2021-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"
        ).astimezone(),
        seen_tiptour=user_data["seen_tiptour"],
        selected_language=user_data.get("selected_language", "en"),
    )


normalData: dict[str, Any] = {
    "auth_name": "TestUser",
    "first_name": "Test",
    "last_name": "User",
    "auth_groups": ["employee"],     
    "admin": False,
    "agreement": "1.0",    
}

adminData: dict[str, Any] = {    
    "auth_name": "AdminUser",
    "first_name": "Admin",
    "last_name": "User",
    "auth_groups": ["employee", "staff"],    
    "admin": True,    
    "agreement": "2.0",    
}


@pytest.fixture
def normal_user(monkeypatch: pytest.MonkeyPatch, mock_repositories : Repositories) -> BackendUser:
    """
    Fixture to a normal user in the authentication scheme.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Monkeypatch fixture

    """

    user = get_backend_user(normalData)
    return user


@pytest.fixture
def admin_user(monkeypatch: pytest.MonkeyPatch) -> BackendUser:
    """
    Fixture to an admin user in the authentication scheme.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Monkeypatch fixture

    """

    user = get_backend_user(adminData)
    return user


@pytest.fixture
def basic_users(mock_repositories: Repositories) -> Generator[Repositories, None, None]:
    mock_repositories.user_repo.users[] = get_db_user(normalData)
    mock_repositories.user_repo.users[2] = get_db_user(adminData)
    mock_repositories.user_repo.set_current_user_id(3)
    yield mock_repositories
    mock_repositories.user_repo.reset()

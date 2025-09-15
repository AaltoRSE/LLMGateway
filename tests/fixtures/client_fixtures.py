from typing import Generator
import os
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from .db_fixtures import mock_repositories, Repositories
import app.main
import app.middleware.authentication_dependency
from app.security.auth import BackendUser, RequestSource
from app.services.user_service import UserService, UserBase, User
from app.services.key_service import KeyService
from app.dbs.redis.redis import get_key_client, get_key_quota_client
from app.security.api_keys import admin_key_header


async def session_auth_mock(arg1, arg2, user: BackendUser) -> BackendUser:
    return user


admin_base = UserBase(
    admin=True,
    auth_id="admin",
    first_name="Admin",
    last_name="User",
    accepted_agreement_version="1.0",
)
normal_base = UserBase(
    admin=False,
    auth_id="user",
    first_name="Test",
    last_name="User",
    accepted_agreement_version="2.0",
)


def build_backend_user(source: RequestSource, user: User) -> BackendUser:
    return BackendUser(username=user.auth_id, request_source=source, isadmin=user.admin)


async def create_user(
    mock_repositories: Repositories, source: RequestSource, user_base: UserBase
):
    user_service = UserService(mock_repositories.user_repo, mock_repositories.key_repo)
    user: User = await user_service.create_new_user(user_base)
    # create a lambda function that returns a Valid backend user.
    return user


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
async def normal_session_user(monkeypatch, mock_repositories):
    user: User = await create_user(mock_repositories, normal_base)
    backend_user = build_backend_user(source=RequestSource(user=user.id))
    monkeypatch.setattr(
        app.middleware.authentication_dependency,
        "get_user_from_session",
        lambda arg1, arg2: session_auth_mock(arg1, arg2, backend_user),
    )


@pytest_asyncio.fixture
async def admin_session_user(monkeypatch, mock_repositories):
    user: User = await create_user(mock_repositories, admin_base)
    backend_user = build_backend_user(source=RequestSource(user=user.id))
    monkeypatch.setattr(
        app.middleware.authentication_dependency,
        "get_user_from_session",
        lambda arg1, arg2: session_auth_mock(arg1, arg2, backend_user),
    )


@pytest_asyncio.fixture
async def user_api_key(mock_repositories, redis_dbs):
    user: User = await create_user(mock_repositories, admin_base)
    key = await create_key(mock_repositories, user)


@pytest.fixture
def normal_session_client(normal_session_user) -> Generator[TestClient, None, None]:
    # By adding the normal user fixture, we make this authed.
    client = TestClient(app.main.app)
    yield client


@pytest.fixture
def admin_session_client(admin_session_user) -> Generator[TestClient, None, None]:
    # By adding the normal user fixture, we make this authed.
    client = TestClient(app.main.app)
    yield client


@pytest.fixture
def key_client(user_api_key) -> Generator[TestClient, None, None]:
    client = TestClient(app.main.app)
    client.headers["Authorization"] = f"Bearer: {user_api_key}"
    yield client


@pytest.fixture
def admin_key_client(user_api_key) -> Generator[TestClient, None, None]:
    os.environ["ADMIN_KEY"] = "TestKey"
    client = TestClient(app.main.app)
    client.headers[admin_key_header.model.name] = f"{os.environ.get('ADMIN_KEY')}"
    yield client


@pytest.fixture
def unauthed_client(setup_repos: None) -> Generator[TestClient, None, None]:
    client = TestClient(app.main.app)
    yield client

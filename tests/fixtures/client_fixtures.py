from typing import Generator
import os
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

import app.main
import app.security.authentication_dependencies
from app.security.auth import BackendUser, RequestSource
from app.services.user_service import User
from app.dbs.redis.redis import get_key_client, get_key_quota_client
from app.security.api_keys import admin_key_header

from tests.fixtures.app_fixtures import setup_repos
from .user_fixtures import normal_user, admin_user
from .key_fixtures import user_api_key


async def session_auth_mock(arg1, arg2, user: BackendUser) -> BackendUser:
    return user


def build_backend_user(source: RequestSource, user: User) -> BackendUser:
    return BackendUser(user_id=user.auth_id, request_source=source, isadmin=user.admin)


@pytest_asyncio.fixture
async def normal_session_user(monkeypatch, mock_repositories, setup_repos, normal_user):
    backend_user = build_backend_user(source=RequestSource(user_id=normal_user.id))
    monkeypatch.setattr(
        app.security.authentication_dependencies,
        "get_user_from_session",
        lambda arg1, arg2: session_auth_mock(arg1, arg2, backend_user),
    )


@pytest_asyncio.fixture
async def admin_session_user(monkeypatch, mock_repositories, setup_repos, admin_user):
    backend_user = build_backend_user(source=RequestSource(user_id=admin_user.id))
    monkeypatch.setattr(
        app.security.authentication_dependencies,
        "get_user_from_session",
        lambda arg1, arg2: session_auth_mock(arg1, arg2, backend_user),
    )


@pytest.fixture
def normal_session_client(
    setup_repos: None, normal_session_user
) -> Generator[TestClient, None, None]:
    # By adding the normal user fixture, we make this authed.
    client = TestClient(app.main.app)
    yield client


@pytest.fixture
def admin_session_client(
    setup_repos: None, admin_session_user
) -> Generator[TestClient, None, None]:
    # By adding the normal user fixture, we make this authed.
    client = TestClient(app.main.app)
    yield client


@pytest.fixture
def key_client(setup_repos: None, user_api_key) -> Generator[TestClient, None, None]:
    client = TestClient(app.main.app)
    client.headers["Authorization"] = f"Bearer: {user_api_key}"
    yield client


@pytest.fixture
def admin_key_client(
    setup_repos: None, user_api_key
) -> Generator[TestClient, None, None]:
    os.environ["ADMIN_KEY"] = "TestKey"
    client = TestClient(app.main.app)
    client.headers[admin_key_header.model.name] = f"{os.environ.get('ADMIN_KEY')}"
    yield client


@pytest.fixture
def unauthed_client(setup_repos: None) -> Generator[TestClient, None, None]:
    client = TestClient(app.main.app)
    yield client

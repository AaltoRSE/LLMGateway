from typing import Generator, AsyncGenerator
import os
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.security.session import get_user_from_session
from app.security.auth import BackendUser, RequestSource
from app.services.user_service import User, UserService
from app.services.key_service import KeyService
from app.dbs.redis.redis import get_key_client, get_key_quota_client
from app.security.api_keys import admin_key_header
from tests.fixtures.app_fixtures import setup_repos
from .user_fixtures import normal_user, admin_user
from .key_fixtures import user_api_key


async def session_auth_mock(arg1, arg2, user: BackendUser) -> BackendUser:
    return user


def build_backend_user(source: RequestSource, user: User) -> BackendUser:

    return BackendUser(
        username=user.id, request_source=source, agreement_ok=True, isadmin=user.admin
    )


@pytest_asyncio.fixture
async def normal_session_client(
    setup_repos: None, llm_gateway: FastAPI, normal_user
) -> AsyncGenerator[TestClient, None]:
    backend_user = build_backend_user(
        source=RequestSource(user_id=normal_user.id, has_session=True), user=normal_user
    )

    async def get_normal_client():
        return backend_user

    # By adding the normal user fixture, we make this authed.
    llm_gateway.dependency_overrides[get_user_from_session] = get_normal_client
    client = TestClient(llm_gateway)

    yield client


@pytest_asyncio.fixture
async def admin_session_client(
    setup_repos: None, admin_user, llm_gateway: FastAPI
) -> AsyncGenerator[TestClient, None]:
    backend_user = build_backend_user(
        source=RequestSource(user_id=admin_user.id, has_session=True), user=admin_user
    )

    async def get_admin_client():
        return backend_user

    llm_gateway.dependency_overrides[get_user_from_session] = get_admin_client

    client = TestClient(llm_gateway)
    yield client


@pytest_asyncio.fixture
async def key_client(
    setup_repos: None, user_api_key, llm_gateway
) -> AsyncGenerator[TestClient, None]:
    client = TestClient(llm_gateway)
    client.headers["Authorization"] = f"Bearer {user_api_key.key}"
    yield client


@pytest.fixture
def admin_key_client(
    mock_repositories, redis_dbs, setup_repos: None, user_api_key, llm_gateway
) -> Generator[TestClient, None, None]:
    os.environ["ADMIN_KEY"] = "TestKey"
    client = TestClient(llm_gateway)
    client.headers[admin_key_header.model.name] = f"{os.environ.get('ADMIN_KEY')}"
    yield client


@pytest.fixture
def unauthed_client(
    setup_repos: None, llm_gateway
) -> Generator[TestClient, None, None]:
    client = TestClient(llm_gateway)
    yield client

from typing import Generator
import pytest
from fastapi.testclient import TestClient

import app.main
from app.security.auth_types import BackendUser

from tests.utils.jwt_utils import create_user_token
from tests.fixtures.app_fixtures import setup_repos, setup_auth




@pytest.fixture
def normal_client(
    setup_auth: None, setup_repos: None, normal_user: BackendUser
) -> Generator[TestClient, None, None]:
    # By adding the normal user fixture, we make this authed.
    client = TestClient(app.main.app)
    token = create_user_token(
        auth_id=normal_user.auth_id,
        groups=normal_user.roles,
        first=normal_user.user.first_name,
        last=normal_user.user.last_name,
    )
    client.headers["Authorization"] = f"{token}"
    yield client


@pytest.fixture
def admin_client(
    setup_auth: None, setup_repos: None, admin_user: BackendUser
) -> Generator[TestClient, None, None]:
    client = TestClient(app.main.app)
    token = create_user_token(
        auth_id=admin_user.auth_id,
        groups=admin_user.roles,
        first=admin_user.user.first_name,
        last=admin_user.user.last_name,
    )
    client.headers["Authorization"] = f"{token}"
    yield client


@pytest.fixture
def unauthed_client(
    setup_auth: None, setup_repos: None
) -> Generator[TestClient, None, None]:
    client = TestClient(app.main.app)
    yield client

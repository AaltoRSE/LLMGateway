from typing import Generator
import pytest
from fastapi import FastAPI

from app.dbs.postgresql.repositories.user_repository import SQLUserRepository
from app.dbs.postgresql.repositories.usage_repository import SQLUsageRepository
import app.repositories.factories
import app.main
import app.security.entra_jwt
from tests.utils.jwt_utils import jwks
from tests.fixtures.db_fixtures import Repositories


@pytest.fixture
def setup_repos(mock_repositories: Repositories) -> Generator[FastAPI, None, None]:
    currentapp = app.main.app
    currentapp.dependency_overrides[SQLUserRepository] = (
        app.repositories.factories.get_user_repository_class()
    )
    currentapp.dependency_overrides[SQLUsageRepository] = (
        app.repositories.factories.get_usage_repository_class()
    )
    yield currentapp
    currentapp.dependency_overrides = {}


# @pytest.fixture
# def setup_auth(monkeypatch: pytest.MonkeyPatch) -> None:
#    auth_service = app.security.entra_jwt.get_entrajwt_auth_service()
#    auth_service._set_jwks(jwks)  # type: ignore

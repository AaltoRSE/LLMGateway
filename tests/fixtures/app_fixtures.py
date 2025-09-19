from typing import AsyncGenerator
import pytest
from fastapi import FastAPI

from app.dbs.postgresql.repositories.user_repository import SQLUserRepository
from app.dbs.postgresql.repositories.balance_repository import SQLBalanceRepository
from app.dbs.postgresql.repositories.model_repository import SQLModelRepository
from app.dbs.postgresql.repositories.api_key_repository import SQLAPIKeyRepositry
from app.dbs.postgresql.repositories.usage_repository import SQLUsageRepository
import app.repositories.factories
import app.main

# import app.security.entra_jwt
# from tests.utils.jwt_utils import jwks
from tests.fixtures.db_fixtures import Repositories


@pytest.fixture
async def setup_repos(mock_repositories: Repositories) -> AsyncGenerator[FastAPI, None]:
    currentapp = app.main.app
    currentapp.dependency_overrides[SQLUserRepository] = (
        await app.repositories.factories.get_user_repository_class()
    )
    currentapp.dependency_overrides[SQLUsageRepository] = (
        await app.repositories.factories.get_usage_repository_class()
    )
    currentapp.dependency_overrides[SQLBalanceRepository] = (
        await app.repositories.factories.get_balance_repository_class()
    )
    currentapp.dependency_overrides[SQLModelRepository] = (
        await app.repositories.factories.get_llm_repository_class()
    )
    currentapp.dependency_overrides[SQLAPIKeyRepositry] = (
        await app.repositories.factories.get_key_repository_class()
    )

    yield currentapp
    currentapp.dependency_overrides = {}


# @pytest.fixture
# def setup_auth(monkeypatch: pytest.MonkeyPatch) -> None:
#    auth_service = app.security.entra_jwt.get_entrajwt_auth_service()
#    auth_service._set_jwks(jwks)  # type: ignore

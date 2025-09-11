from typing import Generator

import pytest

import app.repositories.factories
import app.config.db

from tests.utils.mock_repositories import (
    UserRepositoryImpl,
    LLMModelRepositoryImpl,
    APIKeyRepositoryImpl,
    UsageRepositoryImpl,
    BalanceRepositoryImpl,    
)


class Repositories:
    def __init__(
        self,
        user_repo: UserRepositoryImpl,
        model_repo: LLMModelRepositoryImpl,
        key_repo: APIKeyRepositoryImpl,
        usage_repo: UsageRepositoryImpl,
        balance_repo: BalanceRepositoryImpl,        
    ) -> None:
        self.user_repo: UserRepositoryImpl = user_repo
        self.model_repo: LLMModelRepositoryImpl = model_repo
        self.key_repo: APIKeyRepositoryImpl = key_repo
        self.usage_repo: UsageRepositoryImpl = usage_repo
        self.balance_repo: BalanceRepositoryImpl = balance_repo
        


@pytest.fixture
def mock_repositories(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Repositories, None, None]:
    """
    Fixture to mock the database connection (working around the dbs).

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Monkeypatch fixture

    Returns
    -------
    MagicMock
        The mocked database connection.
    """
    monkeypatch.setattr(app.config.db, "UserRepositoryImpl", UserRepositoryImpl)
    monkeypatch.setattr(
        app.config.db, "LLMModelRepositoryImpl", LLMModelRepositoryImpl
    )
    monkeypatch.setattr(app.config.db, "APIKeyRepositoryImpl", APIKeyRepositoryImpl)
    monkeypatch.setattr(app.config.db, "UsageRepositoryImpl", UsageRepositoryImpl)
    monkeypatch.setattr(app.config.db, "BalanceRepositoryImpl", BalanceRepositoryImpl)
    monkeypatch.setattr(
        app.repositories.factories,
        "get_user_repository_class",
        lambda: UserRepositoryImpl,
    )
    monkeypatch.setattr(
        app.repositories.factories,
        "get_balance_repository_class",
        lambda: BalanceRepositoryImpl,
    )
    monkeypatch.setattr(
        app.repositories.factories,
        "get_llm_repository_class",
        lambda: LLMModelRepositoryImpl,
    )
    monkeypatch.setattr(
        app.repositories.factories,
        "get_usage_repository_class",
        lambda: UsageRepositoryImpl,
    )
    monkeypatch.setattr(
        app.repositories.factories,
        "get_key_repository_class",
        lambda: APIKeyRepositoryImpl,
    )    

    user_repo = UserRepositoryImpl()
    model_repo =  LLMModelRepositoryImpl()
    key_repo =  APIKeyRepositoryImpl()
    usage_repo = UsageRepositoryImpl()
    balance_repo = BalanceRepositoryImpl()

    yield Repositories(
        user_repo=user_repo, model_repo=model_repo, key_repo=key_repo, usage_repo=usage_repo, balance_repo=balance_repo
    )
    user_repo.reset()
    model_repo.reset()
    key_repo.reset()
    usage_repo.reset()
    balance_repo.reset()
    

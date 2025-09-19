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

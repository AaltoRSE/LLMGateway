"""
Service for balance related activities
"""

from typing import Annotated, List
from datetime import datetime

from fastapi import Depends, HTTPException
from app.schemas.usage_schema import Balance, Quota
from app.repositories.factories import (
    get_usage_repository_class,
    get_user_repository_class,
    get_key_repository_class,
    get_balance_repository_class,
)
from app.repositories import (
    UsageRepository,
    UserRepository,
    APIKeyRepository,
    BalanceRepository,
)


class BalanceService:
    """
    A Service handling all balance related activities.
    """

    def __init__(
        self,
        usage_repository: Annotated[
            UsageRepository, Depends(get_usage_repository_class())
        ],
        balance_repository: Annotated[
            BalanceRepository, Depends(get_balance_repository_class())
        ],
        user_repository: Annotated[
            UserRepository, Depends(get_user_repository_class())
        ],
        apikey_repository: Annotated[
            APIKeyRepository, Depends(get_key_repository_class())
        ],
    ) -> None:
        self.usage_repository: UsageRepository = usage_repository
        self.key_repository: APIKeyRepository = apikey_repository
        self.user_repository: UserRepository = user_repository
        self.balance_repository: BalanceRepository = balance_repository

    async def get_key_balance(self, key: str) -> Quota:
        """
        Get the balance for a specific key
        """
        api_key = await self.key_repository.get_key(key)
        if api_key is None:
            raise HTTPException(400, "Invalid key")
        quota = api_key.quota
        if quota is None:
            quota = float("inf")
        balance = await self.balance_repository.get_key_balance(key)
        return Quota(balance_used=balance.balance_used, key=key, quota=quota)

    async def get_user_balance(self, user_id: str) -> Quota:
        """
        Get the balance for a specific user
        """

        user = await self.user_repository.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(400, "Invalid User")
        quota = user.quota
        balance = await self.balance_repository.get_user_balance(user_id)
        return Quota(balance_used=balance.balance_used, user_id=user_id, quota=quota)

    async def add_usage_to_user(self, user_id: str, cost: float) -> None:
        """
        Add usage to a given user
        """
        # if it doesn't exist it will create the key.
        await self.balance_repository.add_usage_to_user(user_id, cost)

    async def add_usage_to_key(self, key: str, cost: float) -> None:
        """
        Add usage to a given key
        """
        # if it doesn't exist it will create the key.
        await self.balance_repository.add_usage_to_key(key, cost)

    async def check_balance_used_up(self, key: str, user_id: str) -> bool:
        """
        Check whether the balance is used up for a given key and user pair.
        """
        user_balance = await self.get_user_balance(user_id)
        key_balance = await self.get_key_balance(key)
        return user_balance.used_up() or key_balance.used_up()

    async def get_user_balances(self) -> List[Balance]:
        """
        Get the current (this month) balances for all users
        """
        user_balances = await self.balance_repository.get_user_balances(
            month=datetime.now()
        )
        return [Balance.model_validate(user_balance) for user_balance in user_balances]

    async def get_key_balances(self) -> List[Balance]:
        """
        Get the current (this month) balances for all keys
        """
        key_balances = await self.balance_repository.get_key_balances(
            month=datetime.now()
        )
        return [Balance.model_validate(key_balance) for key_balance in key_balances]

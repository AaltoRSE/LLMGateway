"""
Service for balance related activities
"""

from typing import Annotated, List
from datetime import datetime

from fastapi import Depends, HTTPException
import redis.asyncio as redis
from app.schemas.usage_schema import Balance, KeyBalance, UserBalance
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
from app.dbs.redis.redis import (
    get_user_balance_client,
    get_key_balance_client,
    get_key_quota_client,
    get_user_quota_client,
)


class BalanceService:  # pylint: disable=too-many-instance-attributes
    """
    A Service handling all balance related activities.
    """

    def __init__(  # pylint: disable=too-many-arguments
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
        user_balance: Annotated[redis.StrictRedis, Depends(get_user_balance_client)],
        key_balance: Annotated[redis.StrictRedis, Depends(get_key_balance_client)],
        key_quota: Annotated[redis.StrictRedis, Depends(get_key_quota_client)],
        user_quota: Annotated[redis.StrictRedis, Depends(get_user_quota_client)],
    ) -> None:
        self.usage_repository: UsageRepository = usage_repository
        self.key_repository: APIKeyRepository = apikey_repository
        self.user_repository: UserRepository = user_repository
        self.balance_repository: BalanceRepository = balance_repository
        self.user_quota: redis.StrictRedis = user_quota
        self.key_quota: redis.StrictRedis = key_quota
        self.key_balance: redis.StrictRedis = key_balance
        self.user_balance: redis.StrictRedis = user_balance

    async def init_balances_and_quotas(self) -> None:
        """
        Initialize the balances and quotas in the redis dbs
        should happen at app startup
        """
        # Refresh Redis from database.
        # The usage repository should be the ground truth.
        user_balances: List[UserBalance] = (
            await self.balance_repository.get_user_balances(month=datetime.now())
        )
        key_balances: List[KeyBalance] = await self.balance_repository.get_key_balances(
            month=datetime.now()
        )
        # clear the dbs.
        await self.key_balance.flushdb()
        await self.user_balance.flushdb()
        await self.key_quota.flushdb()
        await self.user_quota.flushdb()
        for key_balance in key_balances:
            await self.key_balance.set(key_balance.key, key_balance.balance_used)
            await self.key_quota.set(key_balance.key, key_balance.quota)
        for user_balance in user_balances:
            await self.user_balance.set(user_balance.user_id, user_balance.balance_used)
            await self.user_quota.set(user_balance.user_id, user_balance.quota)

    async def get_key_balance(self, key: str) -> Balance:
        """
        Get the balance for a specific key
        """
        quota = await self.key_quota.get(key)
        if quota is None:
            api_key = await self.key_repository.get_key(key)
            if api_key is None:
                raise HTTPException(400, "Invalid key")
            if api_key.quota is not None:
                await self.key_quota.set(key, api_key.quota)
                quota = api_key.quota
            else:
                await self.key_quota.set(
                    key, float("inf")
                )  # There is no limit set on the key, needs to come from the user
                quota = float("inf")
        current_usage = await self.key_balance.get(key)
        if current_usage is None:
            balance = await self.balance_repository.get_key_balance(key)
            self.key_balance.set(key, balance.balance_used)
            return balance
        return Balance(quota=quota, balance_used=float(current_usage))

    async def get_user_balance(self, user_id: str) -> Balance:
        """
        Get the balance for a specific user
        """
        quota = await self.user_quota.get(user_id)
        if quota is None:
            user = await self.user_repository.get_user_by_id(user_id)
            if user is None:
                raise HTTPException(400, "Invalid User")
            await self.user_quota.set(user_id, user.quota)
            quota = user.quota
        current_usage = await self.user_balance.get(user_id)
        if current_usage is None:
            balance = await self.balance_repository.get_user_balance(user_id)
            self.user_balance.set(user_id, balance.balance_used)
            return balance
        return Balance(quota=quota, balance_used=float(current_usage))

    async def add_usage_to_user(self, user_id: str, cost: float) -> None:
        """
        Add usage to a given user
        """
        # if it doesn't exist it will create the key.
        await self.user_balance.incrbyfloat(user_id, cost)
        await self.balance_repository.add_usage_to_user(user_id, cost)

    async def add_usage_to_key(self, key: str, cost: float) -> None:
        """
        Add usage to a given key
        """
        # if it doesn't exist it will create the key.
        await self.key_balance.incrbyfloat(key, cost)
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

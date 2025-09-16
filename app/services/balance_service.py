# This will directly depend on

from datetime import datetime
from typing import Annotated, List
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


class BalanceService:
    def __init__(
        self,
        usage_repository: Annotated[
            UsageRepository, Depends(get_usage_repository_class())
        ],
        balance_repository: Annotated[
            UsageRepository, Depends(get_balance_repository_class())
        ],
        user_repository: Annotated[
            UserRepository, Depends(get_user_repository_class())
        ],
        apikey_repository: Annotated[
            APIKeyRepository, Depends(get_key_repository_class())
        ],
        user_balance=Annotated[redis.StrictRedis, Depends(get_user_balance_client)],
        key_balance=Annotated[redis.StrictRedis, Depends(get_key_balance_client)],
        key_quota=Annotated[redis.StrictRedis, Depends(get_key_quota_client)],
        user_quota=Annotated[redis.StrictRedis, Depends(get_user_quota_client)],
    ):
        self.usage_repository: UsageRepository = usage_repository
        self.key_repository: APIKeyRepository = apikey_repository
        self.user_repository: UserRepository = user_repository
        self.balance_repository: BalanceRepository = balance_repository
        self.user_quota: redis.StrictRedis = user_quota
        self.key_quota: redis.StrictRedis = key_quota
        self.key_balance: redis.StrictRedis = key_balance
        self.user_balance: redis.StrictRedis = user_balance

    async def init_balances_and_quotas(self) -> None:
        # Refresh Redis from database.

        user_balances: List[UserBalance] = (
            await self.balance_repository.get_user_balances(month=datetime.now())
        )
        key_balances: List[KeyBalance] = await self.balance_repository.get_key_balances(
            month=datetime.now()
        )
        for balance in key_balances:
            self.key_balance.set(balance.key, balance.balance_used)
            self.key_quota.set(balance.key, balance.quota)
        for balance in user_balances:
            self.user_balance.set(balance.user_id, balance.balance_used)
            self.user_quota.set(balance.user_id, balance.quota)

    async def get_key_balance(self, key: str) -> Balance:
        quota = await self.key_quota.get()
        if quota is None:
            api_key = await self.key_repository.get_key(key)
            if api_key is None:
                raise HTTPException(400, "Invalid key")
            if api_key.quota is not None:
                self.key_quota.set(key, api_key.quota)
                quota = api_key.quota
            else:
                self.key_quota.set(
                    key, float("inf")
                )  # There is no lmit set on the key, needs to come from the user
                quota = float("inf")
        current_usage = self.key_balance.get(key)
        if current_usage is None:
            current_usage = 0
        return Balance(total_balance=quota, balance_used=current_usage)

    async def get_user_balance(self, user_id: str) -> Balance:
        quota = await self.user_quota.get()
        if quota is None:
            user = await self.user_repository.get_user_by_id(user_id)
            if user is None:
                raise HTTPException(400, "Invalid key")
            self.user_quota.set(user, user.quota)
            quota = user.quota
        current_usage = self.user_balance.get(user_id)
        if current_usage is None:
            current_usage = 0
        return Balance(total_balance=quota, balance_used=current_usage)

    async def add_usage_to_user(self, user_id: str, cost: float) -> None:
        # if it doesn't exist it will create the key.
        await self.user_balance.incrbyfloat(user_id, cost)
        await self.balance_repository.add_usage_to_user(user_id, cost)

    async def add_usage_to_key(self, key: str, cost: float) -> None:
        # if it doesn't exist it will create the key.
        await self.key_balance.incrbyfloat(key, cost)
        await self.balance_repository.add_usage_to_key(key, cost)

    async def check_balance_used_up(self, key: str, user_id: str) -> bool:
        user_balance = await self.get_user_balance(user_id)
        key_balance = await self.get_key_balance(key)
        return user_balance.used_up() or key_balance.used_up()

    async def get_user_balances(self) -> List[Balance]:
        return await self.balance_repository.get_user_balances(month=datetime.now())

    async def get_key_balances(self) -> List[Balance]:
        return await self.balance_repository.get_key_balances(month=datetime.now())

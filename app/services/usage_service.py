"""This module provides Message service functionality"""

from typing import Annotated, List
from datetime import datetime
from fastapi import Depends
from app.repositories import UsageRepository
from app.repositories.factories import (
    get_usage_repository_class,
    get_user_repository_class,
    get_balance_repository_class,
)
from app.repositories.balance_repository import BalanceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.usage_schema import Balance, APIRequest, RequestSource


class UsageService:
    """Service for Message related business logic"""

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
    ) -> None:
        self.usage_repository = usage_repository
        self.balance_repository = balance_repository
        self.user_repository = user_repository

    async def get_current_user_balance(self, user_id: str) -> Balance:
        """
        Get the current balance for a user.

        Args:
            user (str): The user id for whom the balance is being retrieved.

        Returns:
            Balance: The current balance of the user.
        """
        return await self.balance_repository.get_user_balance(user_id)

    async def get_balance_for_request(self, source: RequestSource) -> Balance:
        """
        Get the current balance for the given RequestSource

        Args:
            source (RequestSource): The source for which to obtain a balance

        Returns:
            Balance: The current balance for the request
        """
        if source.has_key():
            assert source.key is not None
            return await self.balance_repository.get_key_balance(source.key)

        assert source.user_id is not None
        return await self.get_current_user_balance(source.user_id)

    async def get_current_key_balance(self, key: str) -> Balance:
        """
        Get the current balance for a key.

        Args:
            key (str): The key for which the balance is being retrieved.

        Returns:
            Balance: The current balance of the key.
        """
        return await self.balance_repository.get_key_balance(key)

    async def log_usage(self, source: RequestSource, usage: APIRequest) -> None:
        """
        Log usage for a user or key based on a given usage request.

        Args:
            source (RequestSource): The source containing user and/or key information.
            usage (APIRequest): The usage data to log.

        Returns:
            None
        """
        await self.usage_repository.log_usage(source=source, usage=usage)
        if source.user_id:
            await self.balance_repository.add_usage_to_user(
                user_id=source.user_id, cost=usage.cost
            )
        if source.key:
            await self.balance_repository.add_usage_to_key(
                key=source.key, cost=usage.cost
            )

    async def get_usage_for_user(
        self,
        user_id: str,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> List[APIRequest]:
        """
        Retrieve usage records for a specific user within an optional time range.
        Args:
            user_id (str): The ID of the user.
            from_time (datetime, optional): Start of the time range for usage records.
                                            Defaults to None.
            to_time (datetime, optional): End of the time range for usage records. Defaults to None.

        Returns:
            List[APIRequest]: A list of usage records for the user within the specified time range.
        """
        return await self.usage_repository.get_usage_details_for_user(
            user_id, from_time=from_time, to_time=to_time
        )

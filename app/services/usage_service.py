"""This module provides Message service functionality"""

from typing import Annotated
from datetime import datetime
from fastapi import Depends
from app.repositories import UsageRepository
from app.repositories.factories import get_usage_repository_class
from app.repositories.balance_repository import BalanceRepository
from app.schemas.usage_schema import Balance, APIRequest, RequestSource
from app.security.auth import BackendUser


class UsageService:
    """Service for Message related business logic"""

    def __init__(
        self,
        usage_repository: Annotated[
            UsageRepository, Depends(get_usage_repository_class())
        ],
        balance_repository: Annotated[BalanceRepository, Depends(BalanceRepository)]
    ) -> None:
        self.usage_repository = usage_repository
        self.balance_repository = balance_repository

    async def get_current_user_balance(self, user: BackendUser) -> Balance:
        """
        Get the current balance for a user.
        :param user: The user for whom the balance is being retrieved
        :return: The current balance of the user
        """
        return self.balance_repository.get_user_balance(user)

    async def get_current_key_balance(self, key: str) -> Balance:
        """
        Get the current balance for a user.
        :param user: The user for whom the balance is being retrieved
        :return: The current balance of the user
        """
        return self.balance_repository.get_key_balance(key)


    
    async def log_usage(self, source : RequestSource, usage: APIRequest) -> None:
        """
        Log usage for a user based on a given usage request.
        :param user: The user for whom the usage is being logged
        :param usage: The usage data to log
        :return: None
        """

        self.usage_repository.log_usage(user_id=source.user, key=source.key, usage=usage)
        if(source.user):
            self.balance_repository.add_usage_to_user(user_id=source.user,cost=usage.cost)
        if(source.key):
            self.balance_repository.add_usage_to_key(key=source.key,cost=usage.cost)

"""
Balance Repository specification
"""

from datetime import datetime
from typing import List

from app.schemas.usage_schema import UserBalance, KeyBalance

# pylint: disable=duplicate-code


class BalanceRepository:
    """
    This class is the base for all implementations of Balance repositories
    """

    async def get_key_balance(self, key: str) -> KeyBalance:
        """
        Retrieve the balance associated with a specific API key.

        Args:
            key (str): The API key for which the balance is to be retrieved.

        Returns:
            KeyBalance: The balance information for the given API key.
        """
        raise NotImplementedError

    async def get_user_balance(self, user_id: str) -> UserBalance:
        """
        Retrieve the balance associated with a specific user.

        Args:
            user_id (str): The user ID for which the balance is to be retrieved.

        Returns:
            UserBalance: The balance information for the given user.
        """
        raise NotImplementedError

    async def get_user_balances(self, month: datetime) -> List[UserBalance]:
        """
        Get the current balances for a specific month (indicated by the datetime)
        for all users

        Args:
            month (str): a datetime with the month set to the current month
        Returns:
            List[UserBalance]: The balances for all users
        """
        raise NotImplementedError

    async def get_key_balances(self, month: datetime) -> List[KeyBalance]:
        """
        Get the current balances for a specific month (indicated by the datetime)
        for all keys

        Args:
            month (str): a datetime with the month set to the current month
        Returns:
            List[KeyBalance]: The balances for all keys
        """
        raise NotImplementedError

    async def add_usage_to_user(self, user_id: str, cost: float) -> None:
        """
        Add a usage cost to a user's balance.

        Args:
            user_id (str): The user ID to which the cost will be added.
            cost (float): The cost to be added to the user's balance.

        Returns:
            None
        """
        raise NotImplementedError

    async def add_usage_to_key(self, key: str, cost: float) -> None:
        """
        Add a usage cost to an API key's balance.

        Args:
            key (str): The API key to which the cost will be added.
            cost (float): The cost to be added to the API key's balance.

        Returns:
            None
        """
        raise NotImplementedError

    async def set_quota_for_key(self, quota: float, key: str) -> None:
        """
        Set a quota for a specific API key.

        Args:
            quota (float): The quota value to be set for the API key.
            key (str): The API key for which the quota is to be set.

        Returns:
            None
        """
        raise NotImplementedError

    async def set_quota_for_user(self, quota: float, user_id: str) -> None:
        """
        Set a quota for a specific user.

        Args:
            quota (float): The quota value to be set for the user.
            user_id (str): The user ID for which the quota is to be set.

        Returns:
            None
        """
        raise NotImplementedError

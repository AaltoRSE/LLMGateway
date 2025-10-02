# This will directly depend on

from datetime import datetime, date
from typing import List
import threading

from app.schemas.usage_schema import Balance, UserBalance, KeyBalance
from app.repositories.balance_repository import BalanceRepository


class TimedBalance(Balance):
    period: date


class MockBalanceRepository(BalanceRepository):
    balance_list: List[TimedBalance] = []
    _lock = threading.Lock()

    def reset(self) -> None:
        self.__class__.balance_list = []

    def _get_balance(
        self, key: str = None, user_id: str = None, requested_date: date = None
    ) -> TimedBalance:
        if requested_date is None:
            current_time = datetime.now()
            requested_date = date(current_time.year, current_time.month, 1)
        for balance in self.__class__.balance_list:
            if balance.period == requested_date and (
                (balance.key is not None and balance.key == key)
                or (balance.user_id is not None and user_id == balance.user_id)
            ):
                return balance
        new_balance = TimedBalance(
            key=key, user_id=user_id, balance_used=0, period=requested_date
        )
        self.__class__.balance_list.append(new_balance)
        return new_balance

    async def get_key_balance(self, key: str) -> Balance:
        """
        Retrieve the current balance associated with a specific API key.

        Args:
            key (str): The API key for which the balance is to be retrieved.

        Returns:
            Balance: The balance information for the given API key.
        """
        return self._get_balance(key=key).model_copy(deep=True)

    async def get_user_balance(self, user_id: str) -> Balance:
        """
        Retrieve the balance associated with a specific user.

        Args:
            user_id (str): The user ID for which the balance is to be retrieved.

        Returns:
            Balance: The balance information for the given user.
        """
        return self._get_balance(user_id=user_id).model_copy(deep=True)

    async def get_user_balances(self, month: datetime) -> List[UserBalance]:
        """
        Get the current balances for a specific month (indicated by the datetime)
        for all users

        Args:
            month (str): a datetime with the month set to the current month
        Returns:
            List[Balance]: The balances for all users
        """
        requestedDate = date(month.year, month.month, 1)
        balances = [
            balance.model_copy()
            for balance in self.__class__.balance_list
            if balance.period == requestedDate and balance.user_id is not None
        ]

        return [
            UserBalance(
                balance_used=balance.balance_used,
                user_id=balance.user_id,
            )
            for balance in balances
        ]

    async def get_key_balances(self, month: datetime) -> List[KeyBalance]:
        """
        Get the current balances for a specific month (indicated by the datetime)
        for all keys

        Args:
            month (str): a datetime with the month set to the current month
        Returns:
            List[Balance]: The balances for all keys
        """
        requestedDate = date(month.year, month.month, 1)
        balances = [
            balance.model_copy()
            for balance in self.__class__.balance_list
            if balance.period == requestedDate and balance.key is not None
        ]

        return [
            UserBalance(balance_used=balance.balance_used, key=balance.key)
            for balance in balances
        ]

    async def add_usage_to_user(self, user_id: str, cost: float) -> None:
        """
        Add a usage cost to a user's balance.

        Args:
            user_id (str): The user ID to which the cost will be added.
            cost (float): The cost to be added to the user's balance.

        Returns:
            None
        """
        with self.__class__._lock:
            print("Updating usage for " + user_id + " With value " + str(cost))
            balance: TimedBalance = self._get_balance(user_id=user_id)
            print("Old balance was: ", balance.balance_used)
            balance.balance_used = balance.balance_used + cost
            print("New balance is: ", balance.balance_used)

    async def add_usage_to_key(self, key: str, cost: float) -> None:
        """
        Add a usage cost to an API key's balance.

        Args:
            key (str): The API key to which the cost will be added.
            cost (float): The cost to be added to the API key's balance.

        Returns:
            None
        """
        with self.__class__._lock:
            balance = self._get_balance(key=key)
            balance.balance_used = balance.balance_used + cost

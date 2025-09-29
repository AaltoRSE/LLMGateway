from fastapi import Depends
from typing import Annotated, List

# DB Specific imports
from sqlalchemy.orm import Session
from sqlalchemy import func, update

from ..models.usage_model import Usage as DBUsage
from ..models.balance_model import Balance as DBBalance
from ..models.key_model import APIKey as DBAPIKey
from ..models.user_model import User as DBUser
from ..db import db as db_dependency

# App imports
from app.repositories.balance_repository import BalanceRepository
from app.schemas.usage_schema import Usage, Balance, APIRequest, UserBalance, KeyBalance
from datetime import datetime, date


class SQLBalanceRepository(BalanceRepository):
    def __init__(self, db: Annotated[Session, Depends(db_dependency.get_db)]):
        self.db = db

    def _convert_balance_to_schema(self, db_balance: DBBalance) -> Balance:
        return Balance(
            balance_used=db_balance.balance_used,
            key=db_balance.key,
            user_id=str(db_balance.user_id) if db_balance.user_id is not None else None,
        )

    def _convert_balance_to_key_schema(self, db_balance: DBBalance) -> KeyBalance:
        assert db_balance.key is not None
        return KeyBalance(
            balance_used=db_balance.balance_used,
            key=db_balance.key,
        )

    def _convert_balance_to_user_schema(self, db_balance: DBBalance) -> UserBalance:
        assert db_balance.user_id is not None
        return UserBalance(
            balance_used=db_balance.balance_used,
            user_id=str(db_balance.user_id),
        )

    async def get_key_balance(self, key: str) -> KeyBalance:
        """
        Retrieve the current balance associated with a specific API key.

        Args:
            key (str): The API key for which the balance is to be retrieved.

        Returns:
            Balance: The balance information for the given API key.
        """
        current_time = datetime.now()
        requestedDate = date(current_time.year, current_time.month, 1)
        result = (
            self.db.query(DBBalance)
            .filter(DBBalance.key == key, DBBalance.period == requestedDate)
            .first()
        )
        if result is None:
            key_result: DBAPIKey | None = (
                self.db.query(DBAPIKey).filter(DBAPIKey.key == key).first()
            )
            assert key_result is not None
            return KeyBalance(key=key, balance_used=0)
        else:
            return self._convert_balance_to_key_schema(result)

    async def get_user_balance(self, user_id: str) -> UserBalance:
        """
        Retrieve the balance associated with a specific user.

        Args:
            user_id (str): The user ID for which the balance is to be retrieved.

        Returns:
            Balance: The balance information for the given user.
        """
        current_time = datetime.now()
        requestedDate = date(current_time.year, current_time.month, 1)
        result = (
            self.db.query(DBBalance)
            .filter(
                DBBalance.user_id == int(user_id), DBBalance.period == requestedDate
            )
            .first()
        )
        if result is None:
            user_result: DBUser | None = (
                self.db.query(DBUser).filter(DBUser.id == int(user_id)).first()
            )
            assert user_result is not None
            return UserBalance(user_id=user_id, balance_used=0)

        else:
            return self._convert_balance_to_user_schema(result)

    async def get_user_balances(self, month: datetime) -> List[UserBalance]:
        """
        Get the current balances for a specific month (indicated by the datetime)
        for all users

        Args:
            month (str): a datetime with the month set to the current month
        Returns:
            List[Balance]: The balances for all users
        """
        current_time = datetime.now()
        requestedDate = date(current_time.year, current_time.month, 1)
        results = (
            self.db.query(DBBalance)
            .filter(DBBalance.user_id.isnot(None), DBBalance.period == requestedDate)
            .all()
        )
        return [self._convert_balance_to_user_schema(result) for result in results]

    async def get_key_balances(self, month: datetime) -> List[KeyBalance]:
        """
        Get the current balances for a specific month (indicated by the datetime)
        for all keys

        Args:
            month (str): a datetime with the month set to the current month
        Returns:
            List[Balance]: The balances for all keys
        """
        current_time = datetime.now()
        requestedDate = date(current_time.year, current_time.month, 1)
        results = (
            self.db.query(DBBalance)
            .filter(DBBalance.key.isnot(None), DBBalance.period == requestedDate)
            .all()
        )
        return [self._convert_balance_to_key_schema(result) for result in results]

    async def add_usage_to_user(self, user_id: str, cost: float) -> None:
        """
        Add a usage cost to a user's balance.

        Args:
            user_id (str): The user ID to which the cost will be added.
            cost (float): The cost to be added to the user's balance.

        Returns:
            None
        """
        current_time = datetime.now()
        requestedDate = date(current_time.year, current_time.month, 1)
        stmt = (
            update(DBBalance)
            .where(DBBalance.user_id == int(user_id), DBBalance.period == requestedDate)
            .values(balance_used=DBBalance.balance_used + cost)
        )
        self.db.execute(stmt)
        self.db.commit()

    async def add_usage_to_key(self, key: str, cost: float) -> None:
        """
        Add a usage cost to an API key's balance.

        Args:
            key (str): The API key to which the cost will be added.
            cost (float): The cost to be added to the API key's balance.

        Returns:
            None
        """
        current_time = datetime.now()
        requestedDate = date(current_time.year, current_time.month, 1)
        stmt = (
            update(DBBalance)
            .where(DBBalance.key == key, DBBalance.period == requestedDate)
            .values(balance_used=DBBalance.balance_used + cost)
        )
        self.db.execute(stmt)
        self.db.commit()

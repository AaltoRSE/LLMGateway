from fastapi import Depends
from typing import Annotated, List

# DB Specific imports
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.usage_model import Usage as DBUsage
from ..models.balance_model import Balance as DBBalance
from ..db import db as db_dependency

# App imports
from app.repositories.usage_repository import UsageRepository
from app.schemas.usage_schema import Usage, Balance, APIRequest, RequestSource
from datetime import datetime, date


class SQLUsageRepository(UsageRepository):
    def __init__(self, db: Annotated[Session, Depends(db_dependency.get_db)]):
        self.db = db

    def _convert_usage_to_schema(self, db_usage: DBUsage) -> APIRequest:
        return APIRequest(
            timestamp=db_usage.timestamp,
            cost=db_usage.cost,
            prompt_tokens=db_usage.prompt_tokens,
            completion_tokens=db_usage.completion_tokens,
            model=db_usage.model,
        )

    def _convert_balance_to_schema(self, db_balance: DBBalance) -> Balance:
        return Balance(
            period=db_balance.period,
            balance_used=db_balance.balance_used,
            total_balance=db_balance.total_balance,
        )

    async def log_usage(
        self, usage: APIRequest, source : RequestSource
    ) -> None:        
        db_usage = DBUsage(
            user_id=int(source.user) if source.user is not None else None,
            key=source.key,
            timestamp=usage.timestamp,
            cost=usage.cost,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            model=usage.model,
        )
        self.db.add(db_usage)
        self.db.commit()
        self.db.refresh(db_usage)

    async def get_usage_for_user_in_range(
        self, user_id: str, from_timestamp: datetime, to_timestamp: datetime
    ) -> Usage:
        usage = (
            self.db.query(
                func.sum(DBUsage.cost).label("total_cost"),
                func.sum(DBUsage.prompt_tokens).label("total_prompt_tokens"),
                func.sum(DBUsage.completion_tokens).label("total_completion_tokens"),
            )
            .filter(
                DBUsage.user_id == int(user_id),
                DBUsage.timestamp >= from_timestamp,
                DBUsage.timestamp <= to_timestamp,
            )
            .one()
        )

        return Usage(
            cost=usage.total_cost,
            prompt_tokens=usage.total_prompt_tokens,
            completion_tokens=usage.total_completion_tokens,
        )

    async def get_usage_for_key_in_range(
        self, key: str, from_timestamp: datetime, to_timestamp: datetime
    ) -> Usage:
        usage = (
            self.db.query(
                func.sum(DBUsage.cost).label("total_cost"),
                func.sum(DBUsage.prompt_tokens).label("total_prompt_tokens"),
                func.sum(DBUsage.completion_tokens).label("total_completion_tokens"),
            )
            .filter(
                DBUsage.api_key == key,
                DBUsage.timestamp >= from_timestamp,
                DBUsage.timestamp <= to_timestamp,
            )
            .one()
        )
        return Usage(
            cost=usage.total_cost,
            prompt_tokens=usage.total_prompt_tokens,
            completion_tokens=usage.total_completion_tokens,
        )

    async def get_usage_details_for_user(self, user_id: str) -> List[APIRequest]:
        usage = (
            self.db.query(DBUsage)
            .filter(
                DBUsage.user_id == int(user_id),
            )
            .all()
        )
        return [self._convert_usage_to_schema(u) for u in usage]

    async def get_usage_details_for_key(self, key: str) -> List[APIRequest]:
        usage = (
            self.db.query(DBUsage)
            .filter(
                DBUsage.api_key == key,
            )
            .all()
        )
        return [self._convert_usage_to_schema(u) for u in usage]

    def _get_db_balance(self, user_id: int, period: datetime) -> tuple[DBBalance, bool]:
        requestedDate = date(period.year, period.month, 1)
        balance = (
            self.db.query(DBBalance)
            .filter(DBBalance.user_id == user_id, DBBalance.period == requestedDate)
            .one()
        )
        new = False
        if not balance:
            new = True
            balance = DBBalance(
                user_id=user_id,
                period=requestedDate,
                total_balance=30,  # FIXME: This needs to be set by some variable.
            )
        return balance, new

    async def get_balance(self, user_id: int, period: datetime) -> Balance:
        balance, new = self._get_db_balance(user_id=user_id, period=period)

        if new:
            self.db.add(balance)
            self.db.commit()

        return self._convert_balance_to_schema(balance)

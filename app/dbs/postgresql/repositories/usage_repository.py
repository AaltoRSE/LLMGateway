from fastapi import Depends
from typing import Annotated, List, Any

# DB Specific imports
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.usage_model import Usage as DBUsage
from ..models.balance_model import Balance as DBBalance
from ..db import db as db_dependency

# App imports
from app.repositories.usage_repository import (
    UsageRepository,
    APIKey,
    KeyData,
    Usage,
    APIRequest,
    RequestSource,
    ModelUsage,
)
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

    async def log_usage(self, usage: APIRequest, source: RequestSource) -> None:
        db_usage = DBUsage(
            user_id=int(source.user_id) if source.user_id is not None else None,
            api_key=source.key,
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
        self, user_id: str, from_time: datetime, to_time: datetime
    ) -> Usage:
        usage = (
            self.db.query(
                func.sum(DBUsage.cost).label("total_cost"),
                func.sum(DBUsage.prompt_tokens).label("total_prompt_tokens"),
                func.sum(DBUsage.completion_tokens).label("total_completion_tokens"),
            )
            .filter(
                DBUsage.user_id == int(user_id),
                DBUsage.timestamp >= from_time,
                DBUsage.timestamp <= to_time,
            )
            .one()
        )

        return Usage(
            cost=usage.total_cost if usage.total_cost is not None else 0,
            prompt_tokens=(
                usage.total_prompt_tokens
                if usage.total_prompt_tokens is not None
                else 0
            ),
            completion_tokens=(
                usage.total_completion_tokens
                if usage.total_completion_tokens is not None
                else 0
            ),
        )

    async def get_usage_for_key_in_range(
        self, key: str, from_time: datetime, to_time: datetime
    ) -> Usage:
        usage = (
            self.db.query(
                func.sum(DBUsage.cost).label("total_cost"),
                func.sum(DBUsage.prompt_tokens).label("total_prompt_tokens"),
                func.sum(DBUsage.completion_tokens).label("total_completion_tokens"),
            )
            .filter(
                DBUsage.api_key == key,
                DBUsage.timestamp >= from_time,
                DBUsage.timestamp <= to_time,
            )
            .one()
        )
        return Usage(
            cost=usage.total_cost if usage.total_cost is not None else 0,
            prompt_tokens=(
                usage.total_prompt_tokens
                if usage.total_prompt_tokens is not None
                else 0
            ),
            completion_tokens=(
                usage.total_completion_tokens
                if usage.total_completion_tokens is not None
                else 0
            ),
        )

    def _query_usage(
        self,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        user_id: str | None = None,  # We will have to convert this to int for the query
        key: str | None = None,
    ) -> List[APIRequest]:
        conditions = []
        if key is None and user_id is None:
            raise ValueError("Need either user id or key id for query")
        if key is not None:
            conditions.append(DBUsage.api_key == key)
        if user_id is not None:
            conditions.append(DBUsage.user_id == int(user_id))
        if from_time is None:
            from_time = datetime.fromtimestamp(0)
        if to_time is None:
            to_time = datetime.now()
        conditions.append(DBUsage.timestamp >= from_time)
        conditions.append(DBUsage.timestamp <= to_time)
        usage = self.db.query(DBUsage).filter(*conditions).all()
        return [self._convert_usage_to_schema(u) for u in usage]

    async def get_usage_details_for_user(
        self,
        user_id: str,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> List[APIRequest]:

        return self._query_usage(user_id=user_id, from_time=from_time, to_time=to_time)

    async def get_usage_details_for_key(
        self,
        key: str,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> List[APIRequest]:

        return self._query_usage(key=key, from_time=from_time, to_time=to_time)

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

    async def get_usage_for_keys(
        self,
        keys: List[APIKey],
    ) -> List[KeyData]:
        now = datetime.now()
        first_of_month = datetime(now.year, now.month, 1, 0, 0, 0)
        total_results = (
            self.db.query(
                DBUsage.api_key,
                func.sum(DBUsage.cost).label("total_cost"),
                func.sum(DBUsage.prompt_tokens).label("total_prompt_tokens"),
                func.sum(DBUsage.completion_tokens).label("total_completion_tokens"),
            )
            .filter(DBUsage.api_key.in_([key.key for key in keys]))
            .group_by(DBUsage.api_key)
            .all()
        )
        recent_results = (
            self.db.query(
                DBUsage.api_key,
                func.sum(DBUsage.cost).label("recent_usage"),
                func.sum(DBUsage.prompt_tokens).label("recent_prompt_tokens"),
                func.sum(DBUsage.completion_tokens).label("recent_completion_tokens"),
            )
            .filter(
                DBUsage.api_key.in_([key.key for key in keys]),
                DBUsage.timestamp >= first_of_month,
            )
            .group_by(DBUsage.api_key)
            .all()
        )
        result = {
            key.key: {
                "name": key.name,
                "key": key.key,
                "total_cost": 0,
                "total_completion_tokens": 0,
                "total_prompt_tokens": 0,
                "current_cost": 0,
                "current_completion_tokens": 0,
                "current_prompt_tokens": 0,
                "quota": key.quota,
            }
            for key in keys
        }

        for elem in total_results:
            result[elem.api_key].update(
                {
                    "key": elem.api_key,
                    "total_cost": elem.total_cost,
                    "total_completion_tokens": elem.total_completion_tokens,
                    "total_prompt_tokens": elem.total_prompt_tokens,
                }
            )
        for elem in recent_results:
            result[elem.api_key].update(
                {
                    "current_cost": elem.recent_cost,
                    "current_completion_tokens": elem.recent_completion_tokens,
                    "current_prompt_tokens": elem.recent_prompt_tokens,
                }
            )

        return [KeyData.model_validate(element) for element in result.values()]

    async def get_usage_details_for_key_per_model(
        self,
        key: str,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> List[ModelUsage]:
        if from_time is None:
            from_time = datetime.fromtimestamp(0)
        if to_time is None:
            to_time = datetime.now()
        total_results = (
            self.db.query(
                DBUsage.model,
                func.sum(DBUsage.cost).label("cost"),
                func.sum(DBUsage.prompt_tokens).label("prompt_tokens"),
                func.sum(DBUsage.completion_tokens).label("completion_tokens"),
            )
            .filter(
                DBUsage.api_key == key,
                DBUsage.timestamp >= from_time,
                DBUsage.timestamp <= to_time,
            )
            .group_by(DBUsage.model)
            .all()
        )
        return [
            ModelUsage(
                prompt_tokens=elem.prompt_tokens,
                completion_tokens=elem.completion_tokens,
                cost=elem.cost,
                model=elem.model,
            )
            for elem in total_results
        ]

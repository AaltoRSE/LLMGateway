"""A mock repository for usage"""

from datetime import date, datetime
from typing import List, Optional, Any
from pydantic import BaseModel
from app.repositories.usage_repository import UsageRepository, APIKey, KeyData
from app.schemas.usage_schema import Usage, APIRequest, Balance, RequestSource


class DataUsage(BaseModel):
    user_id: str | None
    key: str | None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    model: str
    cost: float
    timestamp: datetime

    def in_period(self, period: datetime) -> bool:
        return (
            self.timestamp.year == period.year and self.timestamp.month == period.month
        )


class UsageRepositoryImpl(UsageRepository):
    usage_list: List[DataUsage] = []

    def reset(self) -> None:
        self.__class__.usage_list = []

    async def log_usage(self, usage: APIRequest, source: RequestSource) -> None:
        self.__class__.usage_list.append(
            DataUsage(
                user_id=source.user_id,
                key=source.key,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                model=usage.model,
                cost=usage.cost,
                timestamp=usage.timestamp,
            )
        )

    async def get_usage_for_user_in_range(
        self, user_id: str, from_time: datetime, to_time: datetime
    ) -> Usage:
        relevant_elements = [
            obj
            for obj in self.usage_list
            if obj.user_id == user_id and from_time <= obj.timestamp <= to_time
        ]
        cost = sum(obj.cost for obj in relevant_elements)
        prompt_tokens = sum(
            obj.prompt_tokens
            for obj in relevant_elements
            if obj.prompt_tokens is not None
        )
        completion_tokens = sum(
            obj.completion_tokens
            for obj in relevant_elements
            if obj.completion_tokens is not None
        )
        return Usage(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, cost=cost
        )

    async def get_usage_details_for_user(
        self,
        user_id: str,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> List[APIRequest]:
        if from_time is None:
            from_time = datetime.fromtimestamp(0)
        if to_time is None:
            to_time = datetime.now()
        return [
            APIRequest(
                model=u.model,
                timestamp=u.timestamp,
                prompt_tokens=u.prompt_tokens,
                completion_tokens=u.completion_tokens,
                cost=u.cost,
            )
            for u in self.__class__.usage_list
            if u.user_id == user_id
            and u.timestamp >= from_time
            and u.timestamp <= to_time
        ]

    async def get_usage_for_key_in_range(
        self, key: str, from_time: datetime, to_time: datetime
    ) -> Usage:
        relevant_elements = [
            obj
            for obj in self.usage_list
            if obj.key == key and from_time <= obj.timestamp <= to_time
        ]
        cost = sum(obj.cost for obj in relevant_elements)
        prompt_tokens = sum(
            obj.prompt_tokens
            for obj in relevant_elements
            if obj.prompt_tokens is not None
        )
        completion_tokens = sum(
            obj.completion_tokens
            for obj in relevant_elements
            if obj.completion_tokens is not None
        )
        return Usage(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, cost=cost
        )

    async def get_usage_details_for_key(
        self,
        key: str,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> List[APIRequest]:
        if from_time is None:
            from_time = datetime.fromtimestamp(0)
        if to_time is None:
            to_time = datetime.now()
        return [
            APIRequest(
                model=u.model,
                timestamp=u.timestamp,
                prompt_tokens=u.prompt_tokens,
                completion_tokens=u.completion_tokens,
                cost=u.cost,
            )
            for u in self.__class__.usage_list
            if u.key == key and u.timestamp >= from_time and u.timestamp <= to_time
        ]

    async def get_usage_for_keys(
        self,
        keys: List[APIKey],
    ) -> List[KeyData]:
        now = datetime.now()
        first_of_month = datetime(now.year, now.month, 1, 0, 0, 0)
        data: dict[str, List[APIRequest]] = {key.key: [] for key in keys}
        for elem in self.__class__.usage_list:
            if elem.key in data:
                data[key].append(elem)
        total_results = []
        recent_results = []
        for key in data:
            total_cost = sum([elem.cost for elem in data[key]])
            total_prompt = sum([elem.prompt_tokens for elem in data[key]])
            total_completion = sum([elem.prompt_tokens for elem in data[key]])
            total_results.append((key, total_cost, total_prompt, total_completion))
        for key in data:
            total_cost = sum(
                [elem.cost for elem in data[key] if elem.timestamp >= first_of_month]
            )
            total_prompt = sum(
                [
                    elem.prompt_tokens
                    for elem in data[key]
                    if elem.timestamp >= first_of_month
                ]
            )
            total_completion = sum(
                [
                    elem.prompt_tokens
                    for elem in data[key]
                    if elem.timestamp >= first_of_month
                ]
            )
            recent_results.append((key, total_cost, total_prompt, total_completion))

        result: dict[str, dict[str, Any]] = {
            api_key: {
                "key": api_key,
                "total_cost": total_cost,
                "total_completion_tokens": total_completion_tokens,
                "total_prompt_tokens": total_prompt_tokens,
            }
            for api_key, total_cost, total_prompt_tokens, total_completion_tokens in total_results
        }
        for (
            api_key,
            recent_cost,
            recent_prompt_tokens,
            recent_completion_tokens,
        ) in recent_results:
            result[api_key].update(
                {
                    "recent_cost": recent_cost,
                    "recent_completion_tokens": recent_completion_tokens,
                    "recent_prompt_tokens": recent_prompt_tokens,
                }
            )
        for key in keys:
            result[key.key].update(
                {
                    "quota": key.quota,
                }
            )
        return [KeyData.model_validate(element) for element in result.values()]

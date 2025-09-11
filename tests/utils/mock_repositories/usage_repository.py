"""A mock repository for usage"""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel
from app.repositories.usage_repository import UsageRepository
from app.schemas.usage_schema import Usage, APIRequest, Balance, RequestSource

class DataUsage(BaseModel):
    user_id: str
    key: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    model: str
    cost: float
    timestamp: datetime
    def in_period(self, period: datetime) -> bool:
        return self.timestamp.year == period.year and self.timestamp.month == period.month

class UsageRepositoryImpl(UsageRepository):
    usage_list: List[DataUsage] = []

    def reset(self) -> None:
        self.__class__.usage_list = []

    async def log_request(self, usage: APIRequest, source : RequestSource ) -> None:
        self.__class__.usage_list.append( 
            DataUsage(
                user_id=source.user,
                key= source.key,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                model=usage.model,
                cost=usage.cost,
                timestamp=usage.timestamp
            )
        )


    async def get_usage_for_user_in_range(
        self, user_id: str, from_timestamp: datetime, to_timestamp: datetime
    ) -> Usage:
        relevant_elements = [obj for obj in self.usage_list if obj.user_id == user_id and from_timestamp <= obj.timestamp <= to_timestamp]
        cost = sum(obj.cost for obj in relevant_elements)
        prompt_tokens = sum(obj.prompt_tokens for obj in relevant_elements if obj.prompt_tokens is not None)
        completion_tokens = sum(obj.completion_tokens for obj in relevant_elements if obj.completion_tokens is not None)
        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost
        )
    async def get_usage_details_for_user(self, user_id: str) -> List[APIRequest]:
        return [APIRequest(model=u.model,
            timestamp=u.timestamp,
            prompt_tokens=u.prompt_tokens,
            completion_tokens=u.completion_tokens,
            cost=u.cost
            ) for u in self.__class__.usage_list if u.user_id == user_id]
    

    async def get_usage_for_key_in_range(
        self, key: str, from_timestamp: datetime, to_timestamp: datetime
    ) -> Usage:
        relevant_elements = [obj for obj in self.usage_list if obj.key == key and from_timestamp <= obj.timestamp <= to_timestamp]
        cost = sum(obj.cost for obj in relevant_elements)
        prompt_tokens = sum(obj.prompt_tokens for obj in relevant_elements if obj.prompt_tokens is not None)
        completion_tokens = sum(obj.completion_tokens for obj in relevant_elements if obj.completion_tokens is not None)
        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost
        )
    async def get_usage_details_for_key(self, key : str) -> List[APIRequest]:
        return [APIRequest(model=u.model,
            timestamp=u.timestamp,
            prompt_tokens=u.prompt_tokens,
            completion_tokens=u.completion_tokens,
            cost=u.cost
            ) for u in self.__class__.usage_list if u.key == key]
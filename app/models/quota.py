from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import HTTPException
from typing import List, Optional


class PersistentUsage(BaseModel):
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float  # in Euros
    key: str
    timestamp: datetime
    user: Optional[str] = None


class UsageElements(BaseModel):
    prompt_tokens: int
    total_tokens: int
    completion_tokens: int
    cost: float  # in Euros


DEFAULT_USAGE = UsageElements(
    prompt_tokens=0, total_tokens=0, completion_tokens=0, cost=0
)
DEFAULT_KEY_QUOTA = UsageElements(
    prompt_tokens=1e6, total_tokens=2e6, completion_tokens=1e6, cost=20
)
DEFAULT_USER_QUOTA = UsageElements(
    prompt_tokens=3e6, total_tokens=6e6, completion_tokens=3e6, cost=50
)


class RequestTokens(BaseModel):
    prompt_tokens: int
    completion_tokens: int


class RequestUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    prompt_cost: float
    completion_cost: float


class ElementQuota(BaseModel):
    quota: UsageElements
    usage: UsageElements = Field(default=DEFAULT_USAGE)

    def has_quota_remaining(self):
        # This could potentially be updated.
        return self.quota.cost - self.usage.cost > 0

    def add_request(self, request: RequestUsage):
        self.usage.prompt_tokens += request.prompt_tokens
        self.usage.total_tokens += request.prompt_tokens + request.completion_tokens
        self.usage.completion_tokens += request.completion_tokens
        self.usage.cost += (
            request.prompt_cost * request.prompt_tokens
            + request.completion_cost * request.completion_tokens
        )


class UserQuota(ElementQuota):
    quota: UsageElements = Field(default=DEFAULT_USER_QUOTA)


class KeyQuota(ElementQuota):
    quota: UsageElements = Field(default=DEFAULT_KEY_QUOTA)


class OutOfQuotaException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=429, detail=message)


class Quota(BaseModel):
    def check_quota(self):
        raise NotImplementedError


class TimedQuota(Quota):
    week_quota: ElementQuota
    day_quota: ElementQuota

    def check_quota(self):
        if not self.week_quota.has_quota_remaining():
            raise OutOfQuotaException("Key quota for this week exceeded")
        if not self.day_quota.has_quota_remaining():
            raise OutOfQuotaException("Key quota for today exceeded")


class TimedUserQuota(TimedQuota):
    week_quota: UserQuota
    day_quota: UserQuota


class TimedKeyQuota(TimedQuota):
    week_quota: KeyQuota
    day_quota: KeyQuota


class UserAndKeyQuota(Quota):
    user_quota: TimedUserQuota
    key_quota: TimedKeyQuota

    def check_quota(self):
        self.user_quota.check_quota()
        self.key_quota.check_quota()


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0


class ModelUsage(BaseModel):
    model: str
    usage: UsageInfo


class KeyUsage(BaseModel):
    key: str
    usage: UsageInfo


class KeyPerModelUsage(UsageInfo):
    key: str
    name: str
    usage: List[ModelUsage] = []


class UsagePerKeyForUser(UsageInfo):
    keys: List[KeyPerModelUsage] = []


class PerHourUsage(BaseModel):
    timestamp: datetime
    prompt_tokens: int
    completion_tokens: int
    cost: float


class PerModelUsage(BaseModel):

    model: str
    cost: float
    usage: List[PerHourUsage]


class PerUserUsage(BaseModel):
    user: str
    cost: float
    usage: List[PerHourUsage]

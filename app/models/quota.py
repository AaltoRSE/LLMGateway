from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import HTTPException
from typing import List


class PersistentQuota(BaseModel):
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float  # in Euros
    user: str
    key: str
    timestamp: datetime


class QuotaElements(BaseModel):
    prompt_tokens: int
    total_tokens: int
    completion_tokens: int
    cost: float  # in Euros


DEFAULT_USAGE = QuotaElements(
    prompt_tokens=0, total_tokens=0, completion_tokens=0, cost=0
)
DEFAULT_KEY_QUOTA = QuotaElements(
    prompt_tokens=1e6, total_tokens=2e6, completion_tokens=1e6, cost=20
)
DEFAULT_USER_QUOTA = QuotaElements(
    prompt_tokens=3e6, total_tokens=6e6, completion_tokens=3e6, cost=50
)


class RequestTokens(BaseModel):
    prompt_tokens: int
    completion_tokens: int


class RequestQuota(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    prompt_cost: float
    completion_cost: float


class ElementQuota(BaseModel):
    quota: QuotaElements
    usage: QuotaElements = Field(default=DEFAULT_USAGE)

    def has_quota_remaining(self):
        # This could potentially be updated.
        return self.quota.cost - self.usage.cost > 0

    def add_request(self, request: RequestQuota):
        self.usage.prompt_tokens += request.prompt_tokens
        self.usage.total_tokens += request.prompt_tokens + request.completion_tokens
        self.usage.completion_tokens += request.completion_tokens
        self.usage.cost += (
            request.prompt_cost * request.prompt_tokens
            + request.completion_cost * request.completion_tokens
        )


class UserQuota(ElementQuota):
    quota: QuotaElements = Field(default=DEFAULT_USER_QUOTA)


class KeyQuota(ElementQuota):
    quota: QuotaElements = Field(default=DEFAULT_KEY_QUOTA)


class OutOfQuotaException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=429, detail=message)


class Quota(BaseModel):
    user_quota: UserQuota
    key_quota: KeyQuota

    def check_quota(self):
        if not self.user_quota.has_quota_remaining():
            raise OutOfQuotaException("User quota exceeded")
        if not self.key_quota.has_quota_remaining():
            raise OutOfQuotaException("Key quota exceeded")


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

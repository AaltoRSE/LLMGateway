from datetime import datetime, date
from pydantic import BaseModel, model_validator
from typing import Optional, List
from typing_extensions import Self
from app.config import app_configuration


class Balance(BaseModel):
    balance_used: float
    user_id: Optional[str] = None
    key: Optional[str] = None


class Quota(Balance):
    quota: float

    def used_up(self) -> bool:
        return (
            self.balance_used >= self.quota if self.quota is not None else float("inf")
        )


class KeyBalance(Balance):
    key: str


class UserBalance(Balance):
    user_id: str


class RequestTokens(BaseModel):
    prompt_tokens: int
    completion_tokens: int


class Usage(BaseModel):
    prompt_tokens: int | None = 0
    completion_tokens: int | None = 0
    cost: float  # in Euros


class ModelUsage(Usage):
    model: str


class APIRequest(ModelUsage):
    timestamp: datetime


class RequestSource(BaseModel):
    key: Optional[str] = None
    user_id: Optional[str] = None
    has_session: bool = False

    # We will only get a key as source, if this is based on a key.
    def has_key(self) -> bool:
        return self.key is not None

    @model_validator(mode="after")
    def check_one_source_exists(self) -> Self:
        if self.key is None and self.user_id is None:
            raise ValueError("Missing Source! Either user or key has to be non None")
        return self


class KeyData(BaseModel):
    total_cost: float
    total_prompt_tokens: int
    total_completion_tokens: int
    current_cost: float
    current_prompt_tokens: int
    current_completion_tokens: int
    key: str
    name: str
    quota: Optional[float] = None


class UserAndKeyUsageData(BaseModel):
    usage: Usage
    key_details: List[KeyData]

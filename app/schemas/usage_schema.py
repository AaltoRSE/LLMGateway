from datetime import datetime, date
from pydantic import BaseModel, model_validator
from typing import Optional
from typing_extensions import Self


class Balance(BaseModel):
    balance_used: float
    quota: float = 30
    user_id: Optional[str] = (None,)
    key: Optional[str] = (None,)

    def used_up(self) -> bool:
        return self.balance_used >= self.quota


class KeyBalance(Balance):
    key: str


class UserBalance(Balance):
    user_id: str


class RequestTokens(BaseModel):
    prompt_tokens: int
    completion_tokens: int


class Usage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cost: float  # in Euros


class APIRequest(Usage):
    model: str
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

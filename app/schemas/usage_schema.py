from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional


class Balance(BaseModel):
    balance_used: float
    total_balance: float = 30

    def used_up(self) -> bool:
        return self.balance_used >= self.total_balance


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

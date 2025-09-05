from pydantic import BaseModel
from typing import Optional


class APIKey(BaseModel):
    key: str
    user: Optional[str] = None
    active: bool
    name: Optional[str] = None
    quota: Optional[float] = None

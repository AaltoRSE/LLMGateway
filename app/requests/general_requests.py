from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserRequest(BaseModel):
    username: str


class UserUsageRequest(BaseModel):
    user_id: str
    to_time: Optional[datetime] = None
    from_time: Optional[datetime] = None


class KeyUsageRequest(BaseModel):
    key: str
    to_time: Optional[datetime] = None
    from_time: Optional[datetime] = None


class KeyRequest(BaseModel):
    key: str

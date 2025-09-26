from pydantic import BaseModel
from app.schemas.user_schema import SessionAuthData
from typing import List

SESSION_DATA_FIELD = "backend_session"


class HTTPSession(BaseModel):
    key: str
    user_id: str
    auth_id: str
    roles: List[str]
    ip: str
    data: SessionAuthData
    admin: bool
    agreement_ok: bool
    quota: float

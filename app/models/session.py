from pydantic import BaseModel
from typing import List

SESSION_DATA_FIELD = "backend_session"


class HTTPSession(BaseModel):
    key: str
    user_id: str
    auth_id: str
    roles: List[str]
    ip: str
    data: dict
    admin: bool
    agreement_ok: bool

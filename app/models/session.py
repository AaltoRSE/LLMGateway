from pydantic import BaseModel

SESSION_DATA_FIELD = "backend_session"


class HTTPSession(BaseModel):
    key: str
    user: str
    roles: list
    ip: str
    data: dict
    admin: bool
    agreement_ok: bool

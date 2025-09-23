from pydantic import BaseModel
from typing import Optional
from app.schemas.user_schema import SessionAuthData


class AuthInfo(BaseModel):
    authed: bool
    user: Optional[SessionAuthData] = None
    agreement_ok: Optional[bool] = None
    admin: Optional[bool] = False

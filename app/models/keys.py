from pydantic import BaseModel


class APIKey(BaseModel):
    key: str
    user: str
    active: bool
    name: str
    user_key: bool = True
    has_quota: bool = False
    day_quota: int = 0
    week_quota: int = 0


# class UserKey(BaseModel):
#    user: str
#    key: str

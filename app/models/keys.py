from pydantic import BaseModel


class APIKey(BaseModel):
    key: str
    user: str
    active: bool
    name: str


class UserKey(BaseModel):
    user: str
    key: str

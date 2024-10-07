from pydantic import BaseModel


class UserRequest(BaseModel):
    username: str


class KeyRequest(BaseModel):
    key: str

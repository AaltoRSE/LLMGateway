from typing import List
from app.schemas.user_schema import User
from starlette.authentication import BaseUser

class BackendUser(BaseUser):
    def __init__(self, roles: List[str], user: User, auth_token: str):
        self.roles = roles
        self.user = user
        self.auth_token = auth_token

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.user.first_name + " " + self.user.last_name

    @property
    def auth_id(self) -> str:
        return self.user.auth_id

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def identity(self) -> str:
        return self.auth_id

    def is_admin(self) -> bool:
        return self.user.admin

    def get_roles(self) -> List[str]:
        return self.roles

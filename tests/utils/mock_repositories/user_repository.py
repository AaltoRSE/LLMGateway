"""A mock repository for Users"""

from typing import List, Dict

from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import User, UserBase


class UserRepositoryImpl(UserRepository):
    users: Dict[str, User] = {}    

    def reset(self) -> None:
        self.__class__.users = {}

    def get_user_by_id(self, user_id: str) -> User | None:
        if user_id in self.__class__.users:
            return self.__class__.users[user_id].model_copy(deep=True)
        return None

    def get_user_by_auth_id(self, auth_id: str) -> User | None:
        if auth_id in self.__class__.users:
           return self.__class__.users[auth_id].model_copy(deep=True)
        return None

    def get_all_users(self) -> List[User]:
        return [
            user.model_copy(deep=True) for user in list(self.__class__.users.values())
        ]

    def create_new_user(self, user: UserBase) -> User:        
        if user.auth_id in self.__class__.users:
            raise ValueError("Duplicate User")
        new_user = User(**user.model_dump(), id=user.auth_id)
        self.__class__.users[user.auth_id] = new_user
        return new_user.model_copy(deep=True)

    def update_user(self, user: User) -> User | None:
        if user.id not in self.__class__.users:
            return None
        self.__class__.users[user.id] = user.model_copy(deep=True)
        return user.model_copy(deep=True)

    def delete_user_by_id(self, user_id: str) -> User | None:
        if user_id in self.__class__.users:
            user = self.__class__.users[user_id]
            del self.__class__.users[user_id]
            return user.model_copy(deep=True)
        return None

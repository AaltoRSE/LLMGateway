"""A mock repository for Users"""

from typing import List, Dict
from fastapi import HTTPException
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import User, UserBase, UserUpdate


class UserRepositoryImpl(UserRepository):
    users: Dict[str, User] = {}

    def reset(self) -> None:
        self.__class__.users = {}

    async def get_user_by_id(self, user_id: str) -> User | None:
        if user_id in self.__class__.users:
            return self.__class__.users[user_id].model_copy(deep=True)
        return None

    async def get_user_by_auth_id(self, auth_id: str) -> User | None:
        if auth_id in self.__class__.users:
            return self.__class__.users[auth_id].model_copy(deep=True)
        return None

    async def get_all_users(self) -> List[User]:
        return [
            user.model_copy(deep=True) for user in list(self.__class__.users.values())
        ]

    async def create_new_user(self, user: UserBase) -> User:
        if user.auth_id in self.__class__.users:
            raise HTTPException(409, "Duplicate User")
        new_user = User(**user.model_dump(), id=user.auth_id)
        self.__class__.users[user.auth_id] = new_user
        return new_user.model_copy(deep=True)

    async def update_user(self, user_id: str, update: UserUpdate) -> User | None:
        if user_id not in self.__class__.users:
            return None
        db_user = self.__class__.users[user_id]
        update_data = update.model_dump(exclude_none=True)
        # Only update fields that exist in User
        print(update_data)
        print(update)
        for field in update_data:
            print(f"Updating field {field}")
            if hasattr(db_user, field):
                print(f"Setting {field} to {update_data[field]}")
                setattr(db_user, field, update_data[field])
        return db_user.model_copy(deep=True)

    async def delete_user_by_id(self, user_id: str) -> User | None:
        if user_id in self.__class__.users:
            user = self.__class__.users[user_id]
            del self.__class__.users[user_id]
            return user.model_copy(deep=True)
        return None

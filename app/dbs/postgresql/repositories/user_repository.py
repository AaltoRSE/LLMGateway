"""This module provides user repository functionality"""

from typing import Annotated, List
from fastapi import Depends
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import User, UserBase
from ..models.user_model import User as DBUser
from ..db import db as db_dependency


class SQLUserRepository(UserRepository):
    """Repository for User related database operations"""

    def __init__(self, db_session: Annotated[Session, Depends(db_dependency.get_db)]):
        self.db = db_session

    def _get_dbuser_by_id(self, user_id: str) -> DBUser | None:
        return self.db.query(DBUser).filter(DBUser.id == int(user_id)).first()

    async def get_user_by_id(self, user_id: str) -> User | None:
        user = self._get_dbuser_by_id(user_id)
        if user is None:
            return None
        return self._convert_model_to_schema(user)

    def _convert_model_to_schema(self, db_user: DBUser) -> User:
        return User(
            id=str(db_user.id),
            auth_id=db_user.auth_id,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            admin=db_user.admin,
            accepted_agreement_version=db_user.accepted_agreement_version,
            quota=db_user.quota,
        )

    def _get_db_user_by_auth_id(self, auth_id: str) -> DBUser | None:
        return self.db.query(DBUser).filter(DBUser.auth_id == auth_id).first()

    async def get_user_by_auth_id(self, auth_id: str) -> User | None:
        user = self._get_db_user_by_auth_id(auth_id)
        if user is None:
            return None
        return self._convert_model_to_schema(user)

    async def get_all_users(self) -> List[User]:
        users = self.db.query(DBUser).all()
        return [self._convert_model_to_schema(user) for user in users]

    async def create_new_user(self, user: UserBase) -> User:
        db_user = DBUser(
            auth_id=user.auth_id,
            first_name=user.first_name,
            last_name=user.last_name,
            admin=user.admin,
            accepted_agreement_version=user.accepted_agreement_version,
            quota=user.quota,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._convert_model_to_schema(db_user)

    async def update_user(self, user: User) -> User | None:
        db_user = self._get_db_user_by_auth_id(user.auth_id)
        if db_user is None:
            return None
        db_user.auth_id = user.auth_id
        db_user.first_name = user.first_name
        db_user.last_name = user.last_name
        db_user.admin = user.admin
        db_user.accepted_agreement_version = user.accepted_agreement_version
        db_user.quota = (user.quota,)
        self.db.commit()
        self.db.refresh(db_user)
        return self._convert_model_to_schema(db_user)

    async def delete_user_by_id(self, user_id: str) -> User | None:
        user = self._get_dbuser_by_id(user_id)
        if user is None:
            return None
        self.db.delete(user)
        self.db.commit()
        return self._convert_model_to_schema(user)

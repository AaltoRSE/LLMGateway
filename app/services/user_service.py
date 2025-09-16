"""This module provides User service functionality"""

from typing import List, Annotated
from app.schemas.user_schema import User, UserBase, SessionAuthData
from pymongo import MongoClient
from pymongo import ReturnDocument as Document
import logging
from fastapi import HTTPException, Depends
from app.repositories import UserRepository, APIKeyRepository
from app.services.key_service import KeyService
from app.repositories.factories import (
    get_user_repository_class,
    get_key_repository_class,
)

import os

logger = logging.getLogger("app")


allowedgroups = ["employee", "faculty"]


class UserService:
    """Service for User related business logic"""

    def __init__(
        self,
        user_respository: Annotated[
            UserRepository, Depends(get_user_repository_class())
        ],
        key_service: Annotated[KeyService, Depends(KeyService)],
    ) -> None:
        self.user_respository = user_respository
        self.key_service = key_service

    async def get_user_by_id(self, user_id: str) -> User:
        return await self.user_respository.get_user_by_id(user_id)

    async def get_or_create_user_from_auth_data(
        self, authdata: SessionAuthData
    ) -> User:
        # If the user is not part of the allowed groups, throw an HTTPException

        if len(set(authdata.roles).intersection(allowedgroups)) == 0:
            logger.debug(f"User {authdata.auth_id} is not part of allowed groups")
            raise HTTPException(
                status_code=403,
                detail="Only Staff is allowed to use this service",
            )
        user = await self.get_user_by_id(authdata.auth_id)
        if not user:
            user = await self.create_new_user(
                User(
                    auth_id=authdata.auth_id,
                    first_name=authdata.first_name,
                    last_name=authdata.last_name,
                    admin=False,
                    accepted_agreement_version="0.0",
                )
            )
        # TODO: Potentially Update the user data if it is nt what auth provides!
        return user

    async def get_all_users(self) -> List[User]:

        return await self.user_respository.get_all_users()

    async def update_agreement_version(self, user: User, version: str) -> User | None:
        user.accepted_agreement_version = version
        updated_user = await self.user_respository.update_user(User)
        if updated_user is None:
            raise HTTPException(404, "User not found")
        return updated_user

    async def reset_user(self, user: User):
        user.accepted_agreement_version = "0.0"
        updated_user = await self.user_respository.update_user(user)
        if updated_user is None:
            raise HTTPException(404, "User does not exist")
        self.key_service.deactivate_keys_for_user(user.id)
        return updated_user

    async def create_new_user(self, user: UserBase) -> User:
        return await self.user_respository.create_new_user(user)

    async def delete_user(self, user_id: str):
        await self.user_respository.delete_user_by_id(user_id)

    async def set_admin_status(self, user_id: str, admin: bool):
        user = await self.user_respository.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(404, "User does not exist")
        user.admin = admin
        await self.user_respository.update_user(user)

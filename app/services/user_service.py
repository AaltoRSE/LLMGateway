"""This module provides User service functionality"""

import logging
from typing import List, Annotated

from fastapi import HTTPException, Depends

from app.schemas.user_schema import User, UserBase, SessionAuthData, UserUpdate
from app.repositories import UserRepository
from app.services.key_service import KeyService
from app.repositories.factories import (
    get_user_repository_class,
)

from app.config import app_configuration

logger = logging.getLogger("app")


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

    async def get_user_by_id(self, user_id: str) -> User | None:
        """
        Get user by system id
        """
        return await self.user_respository.get_user_by_id(user_id)

    async def get_user_by_auth_id(self, auth_id: str) -> User | None:
        """
        Get user by auth id
        """
        return await self.user_respository.get_user_by_auth_id(auth_id)

    async def get_or_create_user_from_auth_data(
        self, authdata: SessionAuthData
    ) -> User:
        """
        Create a user based on Auth data from the session or return
        the user if it exists
        """

        # If the user is not part of the allowed groups, throw an HTTPException

        if len(set(authdata.roles).intersection(app_configuration.allowed_groups)) == 0:
            logger.debug("User %s is not part of allowed groups", authdata.auth_id)
            raise HTTPException(
                status_code=403,
                detail="Only Staff is allowed to use this service",
            )
        user = await self.get_user_by_auth_id(authdata.auth_id)
        if not user:
            user = await self.create_new_user(
                UserBase(
                    auth_id=authdata.auth_id,
                    first_name=authdata.first_name,
                    last_name=authdata.last_name,
                    admin=False,
                    accepted_agreement_version="0.0",
                )
            )
        # TODO: Potentially Update the user data if it is nt what auth provides!
        if (
            user.first_name != authdata.first_name
            or user.last_name != authdata.last_name
        ):
            update = UserUpdate(
                last_name=authdata.last_name, first_name=authdata.first_name
            )
            user = await self.user_respository.update_user(
                user_id=user.id, update=update
            )
        assert user is not None
        return user

    async def get_all_users(self) -> List[User]:
        """
        Get all users and their data
        """
        return await self.user_respository.get_all_users()

    async def update_agreement_version(self, user_id: str, version: str) -> User | None:
        """
        Update the agreement version a user has accepted last
        """
        update = UserUpdate(accepted_agreement_version=version)
        updated_user = await self.user_respository.update_user(
            user_id=user_id, update=update
        )
        if updated_user is None:
            raise HTTPException(404, "User not found")
        return updated_user

    async def reset_user(self, user_id: str) -> User:
        """
        Reset a user currently only the agreement version is reset
        """
        update = UserUpdate(accepted_agreement_version="0.0")
        updated_user = await self.user_respository.update_user(user_id, update)
        if updated_user is None:
            raise HTTPException(404, "User does not exist")
        await self.key_service.deactivate_keys_for_user(user_id)
        return updated_user

    async def update_user(self, user_id: str, update: UserUpdate) -> User:
        """
        Update a user with the given update
        """
        user_to_update = await self.get_user_by_id(user_id)
        if user_to_update is None:
            raise HTTPException(404, "User does not exist")
        updated_user = await self.user_respository.update_user(user_id, update)
        assert updated_user is not None
        return updated_user

    async def create_new_user(self, user: UserBase) -> User:
        """
        Ceate a new user given the specified details
        """
        return await self.user_respository.create_new_user(user)

    async def delete_user(self, user_id: str) -> None:
        """
        Delete a user with the given id
        """
        await self.user_respository.delete_user_by_id(user_id)

    async def set_admin_status(self, user_id: str, admin: bool) -> None:
        """
        Set the admin status of a user with the specified id
        """
        user = await self.user_respository.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(404, "User does not exist")
        update = UserUpdate(admin=admin)
        await self.user_respository.update_user(user_id=user_id, update=update)

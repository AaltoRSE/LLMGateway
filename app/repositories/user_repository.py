"""This module provides User repository functionality"""

from typing import List
from app.schemas.user_schema import User, UserBase


class UserRepository:
    """Repository for User related database operations"""

    async def get_user_by_id(self, user_id: str) -> User | None:
        """
        Get a user by their ID.

        Parameters
        ----------
        user_id : str
            The ID of the user to retrieve. Internally we use a str, since this is the only way we can
            make sure, that different db formats are supported equally.

        Returns
        -------
        User | None
            The user with the specified ID, or None if not found.
        """
        raise NotImplementedError

    async def get_user_by_auth_id(self, auth_id: str) -> User | None:
        """
        Get a user by their authentication ID.

        Parameters
        ----------
        auth_id : str
            The authentication ID of the user to retrieve.

        Returns
        -------
        User | None
            The user with the specified authentication ID, or None if not found.
        """
        raise NotImplementedError

    async def get_all_users(self) -> List[User]:
        """
        Get all users.

        Returns
        -------
        List[User]
            A list of all users.
        """
        raise NotImplementedError

    async def create_new_user(self, user: UserBase) -> User:
        """
        Create a new user.

        Parameters
        ----------
        user : UserBase
            The user to create.

        Returns
        -------
        User
            The newly created user.

        Raises
        ------
        HTTPException: 409 if user exists
        """
        raise NotImplementedError

    async def update_user(self, user: User) -> User | None:
        """
        Update an existing user.

        Parameters
        ----------
        user : User
            The user to update.

        Returns
        -------
        User
            The updated user.
        """
        raise NotImplementedError

    async def delete_user_by_id(self, user_id: str) -> User | None:
        """
        Delete a user by their ID.

        Parameters
        ----------
        user_id : int
            The ID of the user to delete.

        Returns
        -------
        User
            The deleted user.
        """
        raise NotImplementedError

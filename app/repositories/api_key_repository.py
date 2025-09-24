"""APIKey Repsitory specification"""

import string
import secrets
from typing import List
from app.schemas.key_schema import APIKey


# pylint: disable=duplicate-code
class APIKeyRepository:
    """Repository for User related database operations"""

    def generate_api_key(self, length: int = 64) -> str:
        """
        Function to generate an API key.

        Parameters:
        - length (int7, optional): Length of the generated API key. Defaults to 64.

        Returns:
        - str: The generated API key.
        """
        alphabet = string.ascii_letters + string.digits
        api_key = "".join(secrets.choice(alphabet) for _ in range(length))
        return api_key

    def build_new_key_object(
        self, user_id: str | None, key: str, service: str | None, name: str
    ) -> APIKey:
        """
        Function to create a new key object.

        Parameters:
        - key (str): The key value.
        - name (str): The name associated with the key.

        Returns:
        - APIKey: A dictionary representing the key object with "active" status, key, and name.
        """
        return APIKey(user_id=user_id, key=key, name=name, active=True, service=service)

    async def create_api_key(
        self, name: str, user_id: str | None = None, service: str | None = None
    ) -> APIKey:
        """
        Create a new API key for a user_id
        """
        raise NotImplementedError

    async def update_key(self, updated_key: APIKey) -> APIKey | None:
        """
        Update a given API key based on it's id.
        """
        raise NotImplementedError

    async def get_active_api_keys_for_user(self, user_id: str) -> List[APIKey]:
        """
        Get all Keys for a user
        """
        raise NotImplementedError

    async def deactivate_keys_for_user(self, user_id: str) -> List[APIKey]:
        """
        Deactivate all keys of a user
        Parameters:
        - user_id (str): the id of the user

        Returns:
        - List[APIKey]: The list of all deactivated keys.

        """
        raise NotImplementedError

    async def deactivate_key(self, key: APIKey) -> bool | None:
        """
        Deactivate a given key. Keys can not be reactivated.
        """
        raise NotImplementedError

    async def get_all_keys(self, active_only: bool = False) -> List[APIKey]:
        """
        Get all keys.
        """
        raise NotImplementedError

    async def get_key(self, key: str) -> APIKey:
        """
        Get a specific key
        """
        raise NotImplementedError

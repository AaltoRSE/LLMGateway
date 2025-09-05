import secrets
import json
import redis.asyncio as redis
import pymongo
from pymongo.errors import DuplicateKeyError

from fastapi import HTTPException, Depends
import logging
from typing import Union, Annotated, List
from app.repositories import APIKeyRepository
from app.repositories.factories import get_key_repository_class
from app.dbs.redis.redis import get_key_client, get_key_quota_client

from app.schemas.key_schema import APIKey

logger = logging.getLogger("app")


class KeyService:
    def __init__(
        self,
        key_repository: Annotated[
            APIKeyRepository, Depends(get_key_repository_class())
        ],
        key_db: Annotated[redis.StrictRedis, Depends(get_key_client)],
        key_quota_db: Annotated[redis.StrictRedis, Depends(get_key_quota_client)],
    ):
        self.repository = key_repository
        self.key_client = key_db
        self.quota_client = key_quota_db

    async def init_keys(self):
        """
        Initialize keys from the database, and check that indexing is set up properly.
        """

        all_keys = await self.repository.get_all_keys()
        activeKeys = {
            x["key"]: json.dumps(APIKey.model_validate(x).model_dump())
            for x in all_keys
        }
        # Clear the current db
        await self.key_client.flushdb()
        # Set up the new one.
        if len(activeKeys) > 0:
            await self.key_client.mset(activeKeys)

    async def get_user_key_if_active(self, key: str) -> Union[APIKey, None]:
        """
        Function to check if a key currently exists. This only checks in Redis,
        not in the persitent storage, as those two should be in sync.

        Parameters:
        - key (str): The key to check.

        Returns:
        - UserKey: A UserKey Object if this key exists, None otherwise
        """
        key_data = await self.key_client.get(key)
        if key_data == None:
            return None
        else:
            # There are only active keys in the redis db.
            return APIKey.model_validate(json.loads(key_data))

    async def delete_key_for_user(self, key: str, user: str):
        """
        Function to delete an existing key for agiven user. only delete
        the key if it exists for this user.

        Parameters:
        - key (str): The key to check.
        - user (str): The user that requests this deletion

        """
        db_key = await self.repository.get_key(key)
        if not db_key is None and db_key.username == user:
            await self.repository.deactivate_key(key)
            await self.key_client.delete(key)

    async def delete_key(self, key: str, user: str = None):
        """
        Function to delete an existing key irrespective of who had that key

        Parameters:
        - key (str): The key to check.

        """
        if user == None:
            await self.repository.deactivate_key(key)
            await self.key_client.delete(key)
        else:
            await self.delete_key_for_user(key=key, user=user)

    async def create_key(self, name: str, user: str | None = None):
        """
        Generates a unique API key and associates it with a specified user.
        The User MUST exist prior to calling this function.
        Args:
        - user: Username of the user to whom the API key will be associated.
        - name: Name or label for the API key.

        Returns:
        - api_key: The generated unique API key associated with the user.
        """
        api_key = await self.repository.create_api_key(user=user, name=name)
        await self._set_key_in_redis(api_key)
        return api_key

    async def _set_key_in_redis(self, api_key: APIKey) -> None:
        await self.key_client.set(api_key.key, json.dumps(api_key.model_dump()))

    async def list_keys(self, user=None) -> List[APIKey]:
        """
        List the available

        Args:
        - user: Username of the user who requests their keys, None if all keys are requested

        Returns:
        - a list of keys in the format [{'key' : key, 'active' : True/False, 'name' : keyname}]
        """

        if user is None:
            return await self.repository.get_all_keys()

        else:
            return await self.repository.get_active_api_keys_for_user(user)

    async def set_key_quota(self, key: str, quota: float):
        """
        Function to set the quota for a key.

        Parameters:
        - key (str): The key to set the quota for.
        - quota (float): The weekly quota for the key.
        """
        api_key = await self.repository.get_key(key)
        api_key.quota = quota
        if api_key is not None:
            await self.repository.update_key(api_key)
            await self.quota_client.set(key, quota)
            await self._set_key_in_redis(key)

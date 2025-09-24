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
        self.key_client: redis.StrictRedis = key_db
        self.quota_client = key_quota_db

    async def init_keys(self) -> None:
        """
        Initialize keys from the database, and check that indexing is set up properly.
        """
        # Load all keys that are active
        all_keys = await self.repository.get_all_keys(active_only=True)
        activeKeys = {x.key: x.model_dump_json() for x in all_keys}
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
            print(f"Got: {APIKey.model_validate(json.loads(key_data))}")
            # There are only active keys in the redis db.
            return APIKey.model_validate(json.loads(key_data))

    async def delete_key_for_user(self, key: str, user_id: str):
        """
        Function to delete an existing key for agiven user. only delete
        the key if it exists for this user.

        Parameters:
        - key (str): The key to check.
        - user_id(str): The user that requests this deletion

        """
        db_key = await self.repository.get_key(key)
        if not db_key is None and db_key.user_id == user_id:
            await self.repository.deactivate_key(db_key)
            await self.key_client.delete(key)
        else:
            if db_key is None:
                raise HTTPException(404, "Key does not exist")
            else:
                logger.warning(
                    f"User {user_id} tried to delete key of a different user"
                )
                raise HTTPException(
                    404,
                    "Key not found",
                )

    async def delete_key(self, key: str, user_id: str = None):
        """
        Function to delete an existing key irrespective of who had that key

        Parameters:
        - key (str): The key to check.

        """
        if user_id == None:
            db_key = await self.repository.get_key(key)
            if db_key is not None:
                await self.repository.deactivate_key(db_key)
                await self.key_client.delete(key)
        else:
            await self.delete_key_for_user(key=key, user_id=user_id)

    async def create_key(
        self, name: str, user_id: str | None = None, service: str | None = None
    ) -> APIKey:
        """
        Generates a unique API key and associates it with a specified user.
        The User MUST exist prior to calling this function.
        Args:
        - user_id Username of the user to whom the API key will be associated.
        - name: Name or label for the API key.

        Returns:
        - api_key: The generated unique API key associated with the user_id
        """
        assert user_id is not None or service is not None
        api_key = await self.repository.create_api_key(
            user_id=user_id, name=name, service=service
        )
        await self._set_key_in_redis(api_key)
        return api_key

    async def _set_key_in_redis(self, api_key: APIKey) -> None:
        await self.key_client.set(api_key.key, json.dumps(api_key.model_dump()))

    async def list_keys(self, user_id: str | None = None) -> List[APIKey]:
        """
        List the available

        Args:
        - user_id Username of the user who requests their keys, None if all keys are requested

        Returns:
        - a list of keys in the format [{'key' : key, 'active' : True/False, 'name' : keyname}]
        """

        if user_id is None:
            return await self.repository.get_all_keys()

        else:
            return await self.repository.get_active_api_keys_for_user(user_id)

    async def set_key_quota(self, key: str, quota: float) -> None:
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

    async def deactivate_keys_for_user(self, user_id: str) -> None:
        """
        Deactivate all keys for a specific user.
        """
        keys = await self.repository.deactivate_keys_for_user(user_id=user_id)
        # Clea up the keys in redis
        for key in keys:
            await self.key_client.delete(key.key)
            await self.quota_client.delete(key.key)

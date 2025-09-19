from app.repositories.api_key_repository import APIKeyRepository, APIKey
from fastapi import Depends

# DB Specific imports
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..db import db as db_dependency

from typing import Annotated, List
from ..models.key_model import APIKey as DBAPIKey


class SQLAPIKeyRepositry(APIKeyRepository):
    """Repository for User related database operations"""

    def __init__(self, db: Annotated[Session, Depends(db_dependency.get_db)]):
        self.db = db

    def _convert_to_db_model(key: APIKey) -> DBAPIKey:
        return DBAPIKey(
            key=key.key,
            user_id=int(key.user_id),
            service=key.service,
            active=key.active,
            name=key.name,
            quota=key.quota,
        )

    def _convert_to_api_model(key: DBAPIKey) -> APIKey:
        return APIKey(
            key=key.key,
            user_id=str(key.user_id),
            active=key.active,
            service=key.service,
            name=key.name,
            quota=key.quota,
        )

    def _get_key_by_id(self, key: str) -> DBAPIKey | None:
        return self.db.query(DBAPIKey).filter(DBAPIKey.key == key).first()

    def _create_new_db_key(self, api_key: APIKey) -> APIKey:
        added = False
        while not added:
            try:
                self.db.add(self._convert_to_db_model(api_key))
                self.db.commit()
                added = True
            except IntegrityError:
                # undo the add and try again.
                self.db.rollback()
                api_key.key = self.generate_api_key()

        return api_key

    async def create_api_key(self, name: str, user_id: str | None = None) -> APIKey:
        """
        Create a new API key for a user
        """
        key = self.generate_api_key()
        api_key: APIKey = self.build_new_key_object(key=key, name=name, user_id=user_id)
        return self._create_new_db_key(api_key)

    async def update_key(self, updated_key: APIKey) -> APIKey | None:
        """
        Update a given API key based on it's id.
        """
        db_key = self._get_key_by_id(updated_key.key)
        if db_key is None:
            return None
        db_key.name = updated_key.name
        db_key.active = updated_key.active
        db_key.quota = updated_key.quota
        self.db.commit()
        self.db.refresh(db_key)
        return self._convert_to_api_model(db_key)

    async def get_active_api_keys_for_user(self, user_id: str) -> List[APIKey] | None:
        """
        Get all Keys for a user
        """
        keys = (
            self.db.query(DBAPIKey)
            .filter(DBAPIKey.user_id == int(user_id), DBAPIKey.active == True)
            .all()
        )
        return [self._convert_to_api_model(key) for key in keys]

    async def deactivate_key(self, key: APIKey) -> bool | None:
        """
        Deactivate a given key. Keys can not be reactivated.
        """
        update = APIKey(key.key, active=False, name=key.name)
        res = self.update_key(update)
        if res:
            return True
        else:
            return None

    async def get_all_keys(self, active_only=False) -> List[APIKey]:
        """
        Get all keys.
        """
        if active_only:

            keys = self.db.query(DBAPIKey).filter(DBAPIKey.active == True).all()
        else:
            keys = self.db.query(DBAPIKey).all()
        return [self._convert_to_api_model(key) for key in keys]

    async def deactivate_keys_for_user(self, user_id: str) -> List[APIKey]:
        """
        Deactivate all keys of a user
        """
        # Get all active keys for the user
        keys = (
            self.db.query(DBAPIKey)
            .filter(DBAPIKey.user_id == int(user_id), DBAPIKey.active == True)
            .all()
        )
        # Deactivate them
        self.db.query(DBAPIKey).filter(DBAPIKey.user_id == int(user_id)).update(
            {DBAPIKey.active: False}, synchronize_session=False
        )
        self.db.commit()
        # Return the list of deactivated keys as APIKey objects
        return [self._convert_to_api_model(key) for key in keys]

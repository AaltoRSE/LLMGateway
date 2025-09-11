"""This module provides User repository functionality"""

import string
import secrets
from typing import List, Dict
from app.schemas.key_schema import APIKey
from app.repositories.api_key_repository import APIKeyRepository


class KeyRepository(APIKeyRepository):
    """Repository for User related database operations"""
    keys: Dict[str, APIKey] = {}    
    current_key = 0
    def reset(self) -> None:
        self.__class__.keys = {}        

    def _create_new_db_key(self, api_key: APIKey) -> APIKey:
        added = False
        while not added:            
            if not api_key.key in self.__class__.keys:
                self.__class__.keys[api_key.key] = api_key                
                added = True
            else :                                
                api_key.key = self.generate_api_key()
        return api_key

    async def create_api_key(self, name: str, user: str | None = None) -> APIKey:
        """
        Create a new API key for a user
        """
        key = self.generate_api_key()
        api_key: APIKey = self.build_new_key_object(key=key, name=name, user=user)
        return self._create_new_db_key(api_key)

    async def update_key(self, updated_key: APIKey) -> APIKey | None:
        """
        Update a given API key based on it's id.
        """
        if updated_key.key in self.__class__.keys:
            changed_key = updated_key.model_copy(deep = True)
            self.__class__.keys[updated_key.key] = changed_key
            return changed_key.model_copy(deep=True)
        else:
            return None
        

    async def get_active_api_keys_for_user(self, userid: str) -> List[APIKey] | None:
        """
        Get all Keys for a user
        """
        return [key.model_copy(deep=True) for key in self.__class__.keys.values() if key.user == userid ]
            

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
            keys = [key.model_copy(deep=True) for key in self.__class__.keys.values() if key.active ]
        else:
            keys = [key.model_copy(deep=True) for key in self.__class__.keys.values() ]
        return keys

    async def deactivate_keys_for_user(self, userid: str) -> None:
        """
        Deactivate all keys of a user
        """
        for key in self.__class__.keys.values():
            if key.user == userid:
                key.active = False        

from app.schemas.llmmodel_schema import LLMModelData

from typing import List
from app.schemas.key_schema import APIKey
from app.schemas.user_schema import User


class LLMModelRepository:
    """Repository for User related database operations"""

    async def get_models(self) -> List[LLMModelData]:
        """
        Get a list of the data of all models
        """
        raise NotImplementedError

    async def get_model(self, id: str) -> LLMModelData | None:
        """
        Get the mode with the given ID
        """
        raise NotImplementedError

    async def add_model(self, model: LLMModelData) -> LLMModelData:
        """
        Add a new model

        Raises:
           ValueError: If the model already exists.
        """
        raise NotImplementedError

    async def update_model(self, model: LLMModelData) -> LLMModelData | None:
        """
        Updtae a model, returns the updated model
        """
        raise NotImplementedError

    async def remove_model(self, id: str) -> bool:
        """
        Remove a model based on its id
        """
        raise NotImplementedError

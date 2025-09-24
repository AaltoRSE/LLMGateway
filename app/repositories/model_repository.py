"""
Model Repository Specification
"""

from typing import List

from app.schemas.llmmodel_schema import LLMModelData


# pylint: disable=duplicate-code
class LLMModelRepository:
    """Repository for Model related database operations"""

    async def get_models(self) -> List[LLMModelData]:
        """
        Get a list of the data of all models
        """
        raise NotImplementedError

    async def get_model(self, model_id: str) -> LLMModelData | None:
        """
        Get the mode with the given ID
        """
        raise NotImplementedError

    async def add_model(self, model: LLMModelData) -> LLMModelData | None:
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

    async def remove_model(self, model_id: str) -> bool:
        """
        Remove a model based on its id
        """
        raise NotImplementedError

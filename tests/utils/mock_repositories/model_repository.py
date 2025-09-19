from app.schemas.llmmodel_schema import LLMModelData
from fastapi import HTTPException
from typing import List, Dict
from app.schemas.key_schema import APIKey
from app.schemas.user_schema import User


class LLMModelRepository:
    """Repository for User related database operations"""

    models: Dict[str, LLMModelData] = {}

    def reset(self) -> None:
        self.__class__.models = {}

    async def get_models(self) -> List[LLMModelData]:
        """
        Get a list of the data of all models
        """
        return [model.model_copy(deep=True) for model in self.__class__.models.values()]

    async def get_model(self, id: str) -> LLMModelData | None:
        """
        Get the mode with the given ID
        """
        if id in self.__class__.models:
            return self.__class__.models[id].model_copy(deep=True)
        return None

    async def add_model(self, model: LLMModelData) -> LLMModelData:
        """
        Add a new model

        Raises:
           ValueError: If the model already exists.
        """
        if model.model.id in self.__class__.models:
            raise HTTPException(409, "Model already exists")
        self.__class__.models[model.model.id] = model.model_copy(deep=True)

    async def update_model(self, model: LLMModelData) -> LLMModelData | None:
        """
        Update a model, returns the updated model
        """
        new_model = None
        if model.model.id in self.__class__.models:
            new_model = model.model_copy(deep=True)
            self.__class__.models[model.model.id] = new_model.model_copy(deep=True)
        return new_model

    async def remove_model(self, id: str) -> bool:
        """
        Remove a model based on its id
        """
        if id in self.__class__.models:
            del self.__class__.models[id]
            return True
        return None

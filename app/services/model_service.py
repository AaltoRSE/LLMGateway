"""
Service for Model administration interaction and model access checks
"""

from typing import List, Annotated, Tuple
import json
import logging

import redis.asyncio as redis
from fastapi import HTTPException, Depends

from app.schemas.llmmodel_schema import (
    LLMModelData,
    LLMModelDataDetails,
)
from app.utils.llm_model import LLMModel
from app.repositories import LLMModelRepository
from app.repositories.factories import get_llm_repository_class
from app.dbs.redis.redis import get_model_client

modelLogger = logging.getLogger("app")


class ModelService:
    """
    Service for Model related actions
    """

    def __init__(
        self,
        llm_repository: Annotated[
            LLMModelRepository, Depends(get_llm_repository_class())
        ],
    ):
        """
        Init function
        """
        self.repository: LLMModelRepository = llm_repository

    async def get_models(self) -> List[LLMModelData]:
        """
        Get all models
        """
        models = await self.repository.get_models()
        return models

    async def get_api_models(self) -> List[LLMModelDataDetails]:
        """
        Function to get all models currently served
        Returns:
        - list: A list of all models available
        """
        models = await self.get_models()
        return [model.model for model in models]

    async def get_model_location(
        self, model_id: str, model_type: str
    ) -> Tuple[str, str]:
        """
        Retrieve the path and host for a specific model and type.

        Args:
            model_id (str): The ID of the model to look up.
            type (str): The type of model usage requested.

        Returns:
            Tuple[str, str]: A tuple containing the model's path and host.

        Raises:
            HTTPException: If the model is not found or cannot be used for the requested type.
        """
        model_data = await self.repository.get_model(model_id)
        if model_data is not None:
            if (
                model_data.model.type is not None
                and model_type in model_data.model.type
            ):
                return model_data.path, model_data.host

            raise HTTPException(
                status_code=404,
                detail=f"Model {model_id} cannot be used for {model_type}",
            )
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    async def get_model(self, model_id: str) -> LLMModel:
        """
        Get the model instance for a specific model
        """
        model_data = await self.repository.get_model(model_id)
        if model_data is not None:
            return LLMModel(model=model_data)
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    async def add_model(self, model: LLMModelData) -> None:
        """
        Function to add a model to the served models
        Returns:
        - list: A list of all models available
        """
        try:
            await self.repository.add_model(model)
        except ValueError as e:
            print(e)
            raise HTTPException(
                status_code=409, detail=f"Model {model.model.id} already exists"
            ) from e

    async def update_model(self, model: LLMModelData) -> None:
        """
        Function to add a model to the served models
        Returns:
        - list: A list of all models available
        """
        exists: LLMModelData | None = await self.repository.update_model(model)

        if exists is None:
            raise HTTPException(
                status_code=410, detail=f"Model {model.model.id} does not exist"
            )

    async def remove_model(self, model: str) -> None:
        """
        Function to remove a model to the served models
        Returns:
        - list: A list of all models available
        """
        deleted = await self.repository.remove_model(model)
        if not deleted:
            raise HTTPException(status_code=410, detail=f"Model {model} does not exist")

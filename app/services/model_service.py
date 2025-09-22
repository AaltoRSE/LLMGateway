import json
import logging
from typing import List, Annotated, Tuple
import redis.asyncio as redis
from fastapi import HTTPException, Depends

from app.schemas.llmmodel_schema import (
    LLMModelDict,
    LLMModelData,
    LLMModelDataDetails,
    model_types,
)
from app.utils.llm_model import LLMModel
from app.repositories import LLMModelRepository
from app.repositories.factories import get_llm_repository_class
from app.dbs.redis.redis import get_model_client
import app.dbs.redis.redis
import app.config.db

modelLogger = logging.getLogger("app")


class ModelService:
    def __init__(
        self,
        llm_repository: Annotated[
            LLMModelRepository, Depends(get_llm_repository_class())
        ],
        model_client: Annotated[redis.StrictRedis, Depends(get_model_client)],
    ):
        self.repository: LLMModelRepository = llm_repository
        self.model_client: redis.StrictRedis = model_client

    async def init_models(self):
        """
        Initialize models from the database, should be called at startup of the server.
        """
        db_models = await self.repository.get_models()
        models = {entry.model.id: entry.model_dump_json() for entry in db_models}

        if len(models) > 0:
            # Clear out anything old.
            await self.model_client.flushdb()
            # We will simply set all models to the redis
            await self.model_client.mset(models)
        else:
            await self.model_client.flushdb()

    async def get_models(self) -> List[LLMModelData]:
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

    async def get_model_location(self, model_id, type: str) -> Tuple[str, str]:
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
        model_data = await self.model_client.get(model_id)
        if model_data:
            requested_model = LLMModelData.model_validate(json.loads(model_data))
            if type in requested_model.model.type:
                return requested_model.path, requested_model.host
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Model {model_id} cannot be used for {type}",
                )
        else:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    async def get_model(self, model_id: str) -> LLMModel:
        print(f"Requestion model: {model_id}")
        print(self.model_client)
        model_data = await self.model_client.get(model_id)
        print(model_data)
        if model_data:
            model_data = LLMModelData.model_validate(json.loads(model_data))
            return LLMModel(model=model_data)
        else:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    async def add_model(self, model: LLMModelData):
        """
        Function to add a model to the served models
        Returns:
        - list: A list of all models available
        """
        try:
            print(f"Adding available model: {model}")
            print(self.model_client)
            new_model = await self.repository.add_model(model)
            await self.model_client.set(model.model.id, new_model.model_dump_json())
        except ValueError as e:
            print(e)
            raise HTTPException(
                status_code=409, detail=f"Model {model.model.id} already exists"
            )

    async def update_model(self, model: LLMModelData):
        """
        Function to add a model to the served models
        Returns:
        - list: A list of all models available
        """
        exists: LLMModelData | None = await self.repository.update_model(model)

        if exists:
            await self.model_client.set(exists.model.id, exists.model_dump_json())
        else:
            raise HTTPException(
                status_code=410, detail=f"Model {model.model.id} does not exist"
            )

    async def remove_model(self, model: str):
        """
        Function to remove a model to the served models
        Returns:
        - list: A list of all models available
        """
        deleted = await self.repository.remove_model(model)
        if deleted:
            # update redis, removing the model
            await self.model_client.delete(model)
        else:
            raise HTTPException(status_code=410, detail=f"Model {model} does not exist")

from fastapi import Depends
from typing import Annotated, List
import pymongo

# DB Specific imports

from pymongo.asynchronous import database, collection

# from ..models.model import LLMModel as DBLLMModel # might become important at some point
from ..db import mongo

# App imports
from app.repositories.model_repository import LLMModelRepository, LLMModelData

# from app.schemas.llmmodel_schema import LLMModelDataDetails


class MongoModelRepository(LLMModelRepository):
    def __init__(
        self, client: Annotated[pymongo.AsyncMongoClient, Depends(mongo.get_client)]
    ):
        self.client = client
        self.db: database.AsyncDatabase = self.client[mongo.DB_NAME]
        self.collection: collection.AsyncCollection = self.db.get_collection(
            mongo.MODEL_COLLECTION
        )

    async def get_models(self) -> List[LLMModelData]:
        """
        Get a list of the data of all models
        """
        res = [
            LLMModelData.model_validate(model)
            async for model in self.collection.find(projection={"_id": 0})
        ]
        return res

    async def get_model(self, id: str) -> LLMModelData | None:
        """
        Get the mode with the given ID
        """
        res = await self.collection.find_one({"model.id": id}, projection={"_id": 0})
        return LLMModelData.model_validate(res)

    async def add_model(self, model: LLMModelData) -> LLMModelData | None:
        """
        Add a new model
        """
        # NOTE: Might need to change this at some point to ensure the ids are unique
        # However, there is not much harm if they are not...
        exists = await self.collection.find_one({"model.id": model.model.id})
        if exists:
            return None
        else:
            await self.collection.insert_one(model.model_dump())
            return model

    async def update_model(self, model: LLMModelData) -> LLMModelData | None:
        """
        Updtae a model, returns the updated model
        """
        exists = await self.collection.find_one_and_update(
            filter={"model.id": model.model.id},
            update=model.model_dump(),
            projection={"_id": False},
        )
        if exists:
            return LLMModelData.model_validate(exists)
        else:
            return None

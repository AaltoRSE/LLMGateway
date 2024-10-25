import json
import logging
from app.models.model import LLMModel, LLMModelDict, LLMModelData
import app.db.redis as redis
import app.db.mongo as mongo
from fastapi import HTTPException
from typing import List

modelLogger = logging.getLogger("app")


class ModelService:
    def __init__(self):
        self.redis_client = redis.redis_model_client
        self.mongo_client = mongo.mongo_client
        self.db = mongo.mongo_client["gateway"]
        self.model_collection = self.db[mongo.MODEL_COLLECTION]

    def init_models(self):
        """
        Initialize models from the database, should be called at startup of the server.
        """
        models = {
            entry["model"]["id"]: json.dumps(entry)
            for entry in self.model_collection.find({}, {"_id": 0})
        }

        if len(models) > 0:
            # Clear out anything old.
            self.redis_client.flushdb()
            # We will simply set all models to the redis
            self.redis_client.mset(models)
        else:
            self.redis_client.delete("models")

    def get_models(self) -> List[LLMModel]:
        models = [
            LLMModel.model_validate(entry)
            for entry in self.model_collection.find({}, {"_id": 0})
        ]
        modelLogger.info(models)
        return models

    def get_api_models(self) -> List[LLMModel]:
        """
        Function to get all models currently served
        Returns:
        - list: A list of all models available
        """
        models = self.get_models()
        return [model.model for model in models]

    def get_model_path(self, model_id):
        model_data = self.redis_client.get(model_id)
        if model_data:
            requested_model = json.loads(model_data)
            return requested_model["path"]
        else:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    def get_model(self, model_id: str) -> LLMModel:
        model_data = self.redis_client.get(model_id)
        if model_data:
            return LLMModel.model_validate(json.loads(model_data))
        else:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    def add_model(self, model: LLMModel):
        """
        Function to add a model to the served models
        Returns:
        - list: A list of all models available
        """
        exists = self.model_collection.find_one({"model.id": model.model.id})
        if exists:
            raise HTTPException(
                status_code=409, detail=f"Model {model.model.id} already exists"
            )
        else:
            self.model_collection.insert_one(model.model_dump())
            # Update the models, setting them.
            # This is the "simple" even though slightly more expensive approach. However, this request
            # will only be run very rarely....
            self.init_models()

    def update_model(self, model: LLMModel):
        """
        Function to add a model to the served models
        Returns:
        - list: A list of all models available
        """
        exists = self.model_collection.find_one({"model.id": model.model.id})
        if exists:
            self.model_collection.update_one(
                {"model.id": model.model.id}, {"$set": model.model_dump()}
            )
            # Update the models, setting them.
            # This is the "simple" even though slightly more expensive approach. However, this request
            # will only be run very rarely....
            self.init_models()
        else:
            raise HTTPException(
                status_code=410, detail=f"Model {model.model.id} does not exist"
            )

    def remove_model(self, model: str):
        """
        Function to remove a model to the served models
        Returns:
        - list: A list of all models available
        """
        exists = self.model_collection.find_one_and_delete({"model.id": model})
        if exists:
            # update redis
            self.init_models()
        else:
            raise HTTPException(status_code=410, detail=f"Model {model} does not exist")

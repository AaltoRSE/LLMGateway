import json
import logging
from app.models.model import LLMModel, LLMModelDict, LLMModelData
import app.db.redis as redis
import app.db.mongo as mongo
from fastapi import HTTPException

modelLogger = logging.getLogger(__name__)


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
            # We will simply set all models to the redis
            self.redis_client.mset(models)
        else:
            self.redis_client.delete("models")

    def load_models(self) -> LLMModelDict:
        return LLMModelDict(
            {
                entry["model"]["id"]: LLMModel.model_validate(entry)
                for entry in self.model_collection.find({}, {"_id": 0})
            }
        )

    def get_models(self):
        """
        Function to get all models currently served
        Returns:
        - list: A list of all models available
        """
        models = self.load_models()
        return [models[model].model for model in models]

    def get_model_path(self, model_id):
        model_data = self.redis_client.get(model_id)
        if model_data:
            requested_model = json.loads(model_data)
            return requested_model["path"]
        else:
            raise HTTPException(status_code=404, detail="Model not found")

    def get_model(self, model_id) -> LLMModel:
        model_data = self.redis_client.get(model_id)
        if model_data:
            return LLMModel.model_validate(json.loads(model_data))
        else:
            raise HTTPException(status_code=404, detail="Model not found")

    def add_model(self, model: LLMModel):
        """
        Function to add a model to the served models
        Returns:
        - list: A list of all models available
        """
        exists = self.model_collection.find_one({"model.id": model.model.id})
        if exists:
            raise HTTPException(status_code=409, detail="Model already exists")
        else:
            self.model_collection.insert_one(model.model_dump())
            # Update the models, setting them.
            # This is the "simple" even though slightly more expensive approach. However, this request
            # will only be run very rarely....
            self.init_models()

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
            raise KeyError("Model does not exist")

import json
import logging
from app.models.model import LLMModel, LLMModelDict, LLMModelData
import app.db.redis as redis
import app.db.mongo as mongo

modelLogger = logging.getLogger(__name__)


class ModelService:
    def __init__(self):
        self.redis_client = redis.redis_model_client
        self.mongo_client = mongo.mongo_client
        self.db = mongo.mongo_client["gateway"]
        self.model_collection = self.db["model"]

    def init_models(self):
        """
        Initialize models from the database, should be called at startup of the server.
        """
        models = LLMModelDict(
            {
                entry["model"]["id"]: LLMModel.model_validate(entry)
                for entry in self.model_collection.find({}, {"model": 1, "path": 1})
            }
        )
        if len(models) > 0:
            # Since this is a root model and the root is a dictionary, it gets "dumped" into a dictionary.
            # Thus, we need to further "dump" it into a string for storage in redis
            self.redis_client.set("models", (json.dumps(models.model_dump())))
        else:
            self.redis_client.delete("models")

    def load_models(self) -> LLMModelDict:
        try:
            return LLMModelDict.model_validate(
                json.loads(self.redis_client.get("models"))
            )
        except:
            return LLMModelDict({})

    def get_models(self):
        """
        Function to get all models currently served
        Returns:
        - list: A list of all models available
        """
        models = self.load_models()
        return [models[model].model for model in models]

    def get_model_path(self, model_id):
        print(model_id)
        try:
            models = self.load_models()
            print(models)
            requested_model = models[model_id]
            if requested_model:
                return requested_model.path
            else:
                return None
        except:
            # Model does not exist
            return None

    def get_model(self, model_id) -> LLMModel:
        try:
            models = self.load_models()
            print(models)
            return models[model_id]
        except:
            # Model does not exist
            return None

    def add_model(self, model: str, owner: str, path: str):
        """
        Function to add a model to the served models
        Returns:
        - list: A list of all models available
        """
        exists = self.model_collection.find_one({"model.id": model})
        if exists:
            raise KeyError("Model already exists")
        else:
            model_model = LLMModel(
                path=path, model=LLMModelData(id=model, owned_by=owner, permissions=[])
            )
            self.model_collection.insert_one(model_model.model_dump())
            # Update the models, setting them.
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

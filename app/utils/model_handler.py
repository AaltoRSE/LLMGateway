import redis
import pymongo
import json
import os
import urllib
import logging


from .api_requests import AddAvailableModelRequest, RemoveModelRequest

modelLogger = logging.getLogger()


def gen_model_object(id, owned_by, path):
    return {
        "data": {
            "id": id,
            "owned_by": owned_by,
            "permissions": [],
            "object": "model",
        },
        "path": path,
    }


class ModelHandler:
    def __init__(self, testing: bool = False):
        if not testing:
            # Needs to be escaped if necessary
            mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER"))
            mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD"))

            mongo_URL = os.environ.get("MONGOHOST")
            # Set up required endpoints.
            mongo_client = pymongo.MongoClient(
                "mongodb://%s:%s@%s/" % (mongo_user, mongo_password, mongo_URL)
            )
            redis_host = os.environ.get("REDISHOST")
            redis_port = os.environ.get("REDISPORT")
            redis_client = redis.StrictRedis(
                host=redis_host, port=int(redis_port), db=0
            )
            self.setup(mongo_client, redis_client)

    def setup(self, mongo_client: pymongo.MongoClient, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.mongo_client = mongo_client
        self.db = mongo_client["gateway"]
        self.model_collection = self.db["model"]
        # Make sure, that key is an index (avoids duplicates);
        self.init_models()

    def init_models(self):
        """
        Initialize models from the database
        """
        models = {
            x["data"]["id"]: gen_model_object(
                x["data"]["id"], x["data"]["owned_by"], x["path"]
            )
            for x in self.model_collection.find({}, {"data": 1, "path": 1})
        }
        # if there are no models we won't init them.
        if len(models) > 0:
            self.redis_client.set("models", json.dumps(models))

    def load_models(self):
        try:
            return json.loads(self.redis_client.get("models"))
        except:
            return {}

    def get_models(self):
        """
        Function to get all models currently served
        Returns:
        - list: A list of all models available
        """
        models = self.load_models()
        return [models[x]["data"] for x in models]

    def get_model_path(self, model_id):
        requested_model = self.load_models()[model_id]
        if requested_model:
            return requested_model["path"]
        else:
            return None

    def add_model(self, model_def: AddAvailableModelRequest):
        """
        Function to add a model to the served models
        Returns:
        - list: A list of all models available
        """
        exists = self.model_collection.find_one({"data.id": model_def.model})
        if exists:
            raise KeyError("Model already exists")
        else:
            self.model_collection.insert_one(
                gen_model_object(
                    model_def.model, model_def.owner, model_def.target_path
                )
            )
            # Update the models, setting them.
            self.init_models()

    def remove_model(self, model_def: RemoveModelRequest):
        """
        Function to remove a model to the served models
        Returns:
        - list: A list of all models available
        """
        exists = self.model_collection.find_one_and_delete({"data.id": model_def.model})
        if exists:
            # update redis
            self.init_models()
        else:
            raise KeyError("Model does not exist")

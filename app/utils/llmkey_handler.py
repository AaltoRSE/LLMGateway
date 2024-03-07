import redis
import pymongo
import os
import urllib


class LLMKeyHandler:
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
        self.key_collection = self.db["llmkey"]
        # Make sure, that username is an index (avoids duplicates when creating keys, which automatically adds a user if necessary);
        self.init_key()

    def init_key(self):
        """
        Initialize keys from the database
        """
        try:
            key = self.key_collection.find_one({})["key"]
            self.redis_client.delete("llmkey")
            # Se the redis key to the obtained key
            self.redis_client.set("llmkey", key)
        except:
            self.redis_client.set("llmkey", "default")

    def set_key(self, key):
        self.redis_client.set("llmkey", key)
        self.key_collection.update_one({}, {"$set": {"key": key}})

    def get_key(self) -> str:
        """
        Get the string value of the current key for the LLM api
        """
        key_value = self.redis_client.get("llmkey")
        if key_value is not None:
            return key_value.decode("utf-8")
        else:
            return "default"

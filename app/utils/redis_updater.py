import redis
import pymongo
import schedule
import time
import urllib
import os

# Needs to be escaped if necessary
mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER"))
mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD"))


class RedisUpdater:
    def __init__(self):
        """
        Initializes Redis and MongoDB connections.
        """
        # Redis connection
        self.redis_client = redis.StrictRedis(host="redis", port=6379, db=0)
        self.entries = []  # Placeholder for entries fetched from MongoDB

        # MongoDB connection
        self.mongo_client = mongo_client = pymongo.MongoClient(
            "mongodb://%s:%s@mongo:27017/" % (mongo_user, mongo_password)
        )
        self.db = mongo_client["gateway"]
        self.keyCollection = db["apikeys"]

    def update_redis(self):
        """
        Updates Redis with API keys fetched from MongoDB.
        """
        # Fetch entries from MongoDB
        self.fetch_entries_from_mongodb()

        # Update Redis with fetched entries
        self.redis_client.rpush("keys", *self.entries)

    def fetch_entries_from_mongodb(self):
        """
        Retrieves active API keys from MongoDB and stores them in self.entries.
        """
        # Retrieve entries from MongoDB
        currentKeys = self.collection.find({"active": True})
        self.entries = [
            entry["APIKEY"] for entry in self.collection.find({}, {"key": 1})
        ]

    def start_scheduler(self):
        """
        Initiates a scheduler to run update_redis every 15 minutes continuously.
        """
        # Schedule the update every 15 minutes
        schedule.every(15).minutes.do(self.update_redis)

        # Run the scheduler continuously
        while True:
            schedule.run_pending()
            # Only do this every 60 seconds - thats often enough.
            time.sleep(60)


# Create an instance of the RedisUpdater and start the scheduler
updater = RedisUpdater()
updater.start_scheduler()

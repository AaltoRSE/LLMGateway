import pymongo
from datetime import datetime
import os
import urllib
import logging

logger = logging.getLogger("app")


def model_usage_pipeline(
    model: str = None,
    from_time: datetime = datetime.fromtimestamp(0),
    to_time: datetime = None,
):
    if to_time == None:
        to_time = datetime.now()
    if model == None:
        search = ({"$match": {"timestamp": {"$gte": from_time, "$lte": to_time}}},)
    else:
        search = {
            "$match": {
                "model": model,
                "timestamp": {"$gte": from_time, "$lte": to_time},
            }
        }
    pipeline = [
        {
            "$lookup": {
                "from": "apikeys",
                "localField": "key",
                "foreignField": "key",
                "as": "key_info",
            }
        },
        {"$unwind": "$key_info"},
        search,
        {
            "$group": {
                "_id": "$key_info.key",
                "total_tokens": {"$sum": "$tokencount"},
                "keys": {
                    "$addToSet": {
                        "name": "$key_info.name",
                        "token_count": "$tokencount",
                    }
                },
            }
        },
        {"$project": {"_id": 0, "total": "$total_tokens", "keys": "$keys"}},
    ]
    return pipeline


def obtain_key_usage(
    keys,
    model: str = None,
    from_time: datetime = datetime.fromtimestamp(0),
    to_time: datetime = None,
):
    base_match = {
        "source": {"$in": keys},
        "sourcetype": "apikey",
        "timestamp": {"$gte": from_time, "$lte": to_time},
    }
    if not model == None:
        base_match["model"] = model
    if to_time == None:
        to_time = datetime.now()
    pipeline = [
        # Match logs based on the selected keys
        {"$match": base_match},
        {
            "$group": {
                "_id": {"source": "$source", "model": "$model"},
                "tokencount": {"$sum": "$tokencount"},
            }
        },
        {
            "$group": {
                "_id": "$_id.source",
                "tokencount": {"$sum": "$tokencount"},
                "models": {
                    "$push": {"model": "$_id.model", "tokencount": "$tokencount"}
                },
            }
        },
        {
            "$lookup": {
                "from": "apikeys",
                "localField": "_id",
                "foreignField": "key",
                "as": "key_info",
            }
        },
        {"$unwind": "$key_info"},
        {
            "$project": {
                "_id": 0,
                "key_name": "$key_info.name",
                "key": "$_id",
                "tokencount": 1,
                "models": 1,
            }
        },
    ]
    return pipeline


# Needs to be escaped if necessary
class LoggingHandler:
    def __init__(self, testing=False):
        if not testing:
            mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER"))
            mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD"))
            mongo_URL = os.environ.get("MONGOHOST")
            # Set up required endpoints.
            mongo_client = pymongo.MongoClient(
                "mongodb://%s:%s@%s/" % (mongo_user, mongo_password, mongo_URL)
            )
            self.setup(mongo_client)

    def setup(self, mongo_client):
        self.db = mongo_client["gateway"]
        self.log_collection = self.db["logs"]
        self.key_collection = self.db["apikeys"]
        self.user_collection = self.db["users"]

    def create_log_entry(self, tokencount, model, source, sourcetype="apikey"):
        """
        Function to create a log entry.

        Parameters:
        - tokencount (int): The count of tokens.
        - model (str): The model related to the log entry.
        - source (str): The source that authorized the request that is being logged. This could be a user name or an apikey.
        - sourcetype (str): Specification of what kind of source authorized the request that is being logged (either 'apikey' or 'user').

        Returns:
        - dict: A dictionary representing the log entry with timestamp.
        """
        return {
            "tokencount": tokencount,
            "model": model,
            "source": source,
            "sourcetype": sourcetype,
            "timestamp": datetime.now(),  # Current timestamp in UTC
        }

    def log_usage_for_key(self, tokencount, model, key):
        """
        Function to log usage for a specific key.

        Parameters:
        - tokencount (int): The count of tokens used.
        - model (str): The model associated with the usage.
        - key (str): The key for which the usage is logged.
        """
        log_entry = self.create_log_entry(
            tokencount=tokencount, model=model, source=key
        )
        self.log_collection.insert_one(log_entry)

    def log_usage_for_user(self, tokencount, model, user):
        """
        Function to log usage for a specific user.

        Parameters:
        - tokencount (int): The count of tokens used.
        - model (str): The model associated with the usage.
        - user (str): The user for which the usage is logged.
        """
        log_entry = self.create_log_entry(
            tokencount=tokencount, model=model, source=user, sourcetype="user"
        )
        self.log_collection.insert_one(log_entry)

    def get_usage_for_user(
        self,
        username: str,
        from_time: datetime = datetime.fromtimestamp(0),
        to_time: datetime = None,
    ):
        if to_time == None:
            to_time = datetime.now()
        # we retrieve all data for the user
        # First, we get all keys for the user
        userData = self.user_collection.find_one({"username": username})
        if userData == None:
            # The user has no entry yet.
            logger.debug("No user data, returning empty info")
            return {"keys": {}, "total_use": 0}
        logger.debug(userData)
        data = self.get_usage_for_keys(userData["keys"])
        logger.debug(data)
        total_use = sum([element["usage"] for element in data])
        logger.debug({"total_use": total_use, "keys": data})
        return {"total_use": total_use, "keys": data}

    def get_usage_for_keys(
        self,
        restrict_to_keys,
        from_time: datetime = datetime.fromtimestamp(0),
        to_time: datetime = None,
    ):
        if to_time == None:
            to_time = datetime.now()
        logger.debug(
            obtain_key_usage(restrict_to_keys, from_time=from_time, to_time=to_time)
        )
        pipeline = obtain_key_usage(
            restrict_to_keys, from_time=from_time, to_time=to_time
        )
        logger.debug(pipeline[0]["$match"])
        logger.debug([x for x in self.log_collection.find(pipeline[0]["$match"])])
        key_info = self.key_collection.find({"key": {"$in": restrict_to_keys}})
        key_data = self.log_collection.aggregate(
            obtain_key_usage(restrict_to_keys, from_time=from_time, to_time=to_time)
        )
        key_data = [entry for entry in key_data]
        logger.debug(key_data)
        key_info = [entry for entry in key_info]
        result = []
        keys_with_usage = []
        for entry in key_data:
            keys_with_usage.append(entry["key"])
            result.append(
                {
                    "key": entry["key"],
                    "name": entry["key_name"],
                    "usage": entry["tokencount"],
                    "modeldata": entry["models"],
                }
            )
        no_use_keys = list(set(restrict_to_keys) - set(keys_with_usage))
        logger.debug(no_use_keys)
        logger.debug([entry for entry in key_info])
        for keydata in key_info:
            logger.debug(keydata)
            if keydata["key"] in no_use_keys:
                result.append(
                    {
                        "key": keydata["key"],
                        "name": keydata["name"],
                        "usage": 0,
                        "modeldata": [],
                    }
                )
        return result

    def get_usage_for_model(
        self,
        model: str,
        from_time: datetime = datetime.fromtimestamp(0),
        to_time: datetime = None,
    ):
        if to_time == None:
            to_time = datetime.now()

        result = self.db.users.aggregate(
            model_usage_pipeline(model, from_time, to_time)
        )
        return [
            {
                "key": entry["key"],
                "name": entry["key_name"],
                "usage": entry["total_tokens"],
            }
            for entry in result
        ]

    def get_usage_for_time_range(
        self,
        from_time: datetime,
        to_time: datetime = None,
        model: str = None,
        user: str = None,
    ):
        base_match = {
            "timestamp": {"$gte": from_time},
        }
        if not model == None:
            base_match["model"] = model
        if not to_time == None:
            base_match["timestamp"] = {"$gte": from_time, "$lte": to_time}
        if not user == None:
            keys = [
                entry.key
                for entry in self.key_collection.aggregate(
                    [{"$match": {"user": user}}, {"$project": {"_id": 0, "key": 1}}]
                )
            ]
            if len(keys) == 0:
                return {"total_usage": 0, "data": []}
            else:
                base_match["source"] = {"$in": keys}

        pipeline = [
            {"$match": base_match},
            {"$group": {"_id": "sum", "tokencount": {"$sum": "$tokencount"}}},
        ]
        return self.log_collection.aggregate(pipeline)[0]["tokencount"]

    def get_usage_by_user(
        self,
        from_time: datetime = datetime.fromtimestamp(0),
        to_time: datetime = None,
        model: str = None,
        user: str = None,
    ):
        base_match = {
            "timestamp": {"$gte": from_time},
        }
        if not model == None:
            base_match["model"] = model
        if not to_time == None:
            base_match["timestamp"] = {"$gte": from_time, "$lte": to_time}
        if not user == None:
            keys = [
                entry.key
                for entry in self.key_collection.aggregate(
                    [{"$match": {"user": user}}, {"$project": {"_id": 0, "key": 1}}]
                )
            ]
            # Source can also be the user themselves
            keys.append(user)
            if len(keys) == 0:
                return {"total_usage": 0, "data": []}
            else:
                base_match["source"] = {"$in": keys}

        pipeline = [
            {"$match": base_match},
            {
                "$lookup": {
                    "from": "apikeys",
                    "localField": "source",
                    "foreignField": "key",
                    "as": "key_info",
                }
            },
            {
                "$addFields": {
                    "user": {
                        "$cond": {
                            "if": {"$eq": ["$sourcetype", "user"]},
                            "then": "$source",
                            "else": {"$arrayElemAt": ["$key_info.user", 0]},
                        }
                    }
                }
            },
            {
                "$project": {
                    "user": 1,
                    "tokencount": 1,
                    "timestamp": 1,
                    "model": 1,
                    "_id": 0,
                }
            },
        ]
        res = list(self.log_collection.aggregate(pipeline))
        logger.info(res)
        return [result for result in res]

from pytest_mock_resources import create_redis_fixture
from pytest_mock_resources import create_mongo_fixture
from key_handler import KeyHandler
import redis
import pymongo

redis = create_redis_fixture()
mongo = create_mongo_fixture()


def test_check_key(redis, mongo):
    handler = KeyHandler(True)
    handler.setup(mongo, redis)
    keys = ["ABC", "DEF"]
    redis.sadd("keys", *keys)
    assert handler.check_key("ABC") == True
    assert handler.check_key("DEF") == True
    assert handler.check_key("BCE") == False


def test_create_key(redis, mongo):
    handler = KeyHandler(True)
    handler.setup(mongo, redis)
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    user_collection = db["users"]
    key_collection = db["apikeys"]
    assert user_collection.count_documents({}) == 1
    user = user_collection.find_one({})
    assert user["username"] == "NewUser"
    assert len(user["keys"]) == 1
    assert key_collection.count_documents({}) == 1
    assert handler.check_key(newKey) == True


def test_delete_key_for_user(redis, mongo):
    handler = KeyHandler(True)
    handler.setup(mongo, redis)
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    user_collection = db["users"]
    key_collection = db["apikeys"]
    assert user_collection.count_documents({}) == 1
    assert key_collection.count_documents({}) == 1
    assert handler.check_key(newKey) == True
    handler.delete_key(newKey, "NewUser")
    user = user_collection.find_one({})
    assert user["username"] == "NewUser"
    assert len(user["keys"]) == 0
    assert key_collection.count_documents({}) == 0
    assert handler.check_key(newKey) == False


def test_set_key_activity(redis, mongo):
    handler = KeyHandler(True)
    handler.setup(mongo, redis)
    # Create key
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    user_collection = db["users"]
    key_collection = db["apikeys"]
    # Make sure key is valid at start
    assert handler.check_key(newKey) == True
    # deactivate key
    handler.set_key_activity(newKey, "NewUser", False)
    key_data = key_collection.find_one({"key": newKey})
    assert key_data["active"] == False
    # Ensure key still exists
    user = user_collection.find_one({"username": "NewUser"})
    assert len(user["keys"]) == 1
    # and key is inactive
    assert handler.check_key(newKey) == False
    # reactivate and test that the key is now active again
    handler.set_key_activity(newKey, "NewUser", True)
    key_data = key_collection.find_one({"key": newKey})
    assert key_data["active"] == True
    assert handler.check_key(newKey) == True

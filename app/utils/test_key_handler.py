from pytest_mock_resources import create_redis_fixture
from pytest_mock_resources import create_mongo_fixture
from key_handler import key_handler
import redis
import pymongo

redis = create_redis_fixture()
mongo = create_mongo_fixture()


def test_check_key(redis, mongo):
    handler = key_handler(True)
    handler.setup(mongo, redis)
    keys = ["ABC", "DEF"]
    redis.sadd("keys", *keys)
    assert handler.check_key("ABC") == True
    assert handler.check_key("DEF") == True
    assert handler.check_key("BCE") == False


def test_create_key(redis, mongo):
    handler = key_handler(True)
    handler.setup(mongo, redis)
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    userCollection = db["users"]
    keyCollection = db["apikeys"]
    assert userCollection.count_documents({}) == 1
    user = userCollection.find_one({})
    assert user["username"] == "NewUser"
    assert len(user["keys"]) == 1
    assert keyCollection.count_documents({}) == 1
    assert handler.check_key(newKey) == True


def test_delete_key(redis, mongo):
    handler = key_handler(True)
    handler.setup(mongo, redis)
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    userCollection = db["users"]
    keyCollection = db["apikeys"]
    assert userCollection.count_documents({}) == 1
    assert keyCollection.count_documents({}) == 1
    assert handler.check_key(newKey) == True
    handler.delete_key(newKey, "NewUser")
    user = userCollection.find_one({})
    assert user["username"] == "NewUser"
    assert len(user["keys"]) == 0
    assert keyCollection.count_documents({}) == 0
    assert handler.check_key(newKey) == False


def test_set_key_activity(redis, mongo):
    handler = key_handler(True)
    handler.setup(mongo, redis)
    # Create key
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    userCollection = db["users"]
    keyCollection = db["apikeys"]
    # Make sure key is valid at start
    assert handler.check_key(newKey) == True
    # deactivate key
    handler.set_key_activity(newKey, "NewUser", False)
    key_data = keyCollection.find_one({"key": newKey})
    assert key_data["active"] == False
    # Ensure key still exists
    user = userCollection.find_one({"username": "NewUser"})
    assert len(user["keys"]) == 1
    # and key is inactive
    assert handler.check_key(newKey) == False
    # reactivate and test that the key is now active again
    handler.set_key_activity(newKey, "NewUser", True)
    key_data = keyCollection.find_one({"key": newKey})
    assert key_data["active"] == True
    assert handler.check_key(newKey) == True

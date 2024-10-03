from pytest_mock_resources import create_redis_fixture
from pytest_mock_resources import create_mongo_fixture
from app.services.key_service import KeyService
import app.db.mongo
import app.db.redis

redis = create_redis_fixture()
mongo = create_mongo_fixture()


# Testing whether keys are checked correctly
def test_check_key(redis, mongo, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongo)
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    keys = {
        "ABC": '{"user" : "a", "key" : "ABC"}',
        "DEF": '{"user" : "a", "key" : "DEF"}',
    }
    redis.mset(keys)
    assert not handler.check_key("ABC") == None
    assert not handler.check_key("DEF") == None
    assert handler.check_key("BCE") == None


# Testing whether keys are created correctly
def test_create_key(redis, mongo, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongo)
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    user_collection = db["users"]
    key_collection = db["apikeys"]
    assert user_collection.count_documents({}) == 1
    user = user_collection.find_one({})
    assert user["username"] == "NewUser"
    assert len(user["keys"]) == 1
    assert key_collection.count_documents({}) == 1
    assert not handler.check_key(newKey) == None


def test_delete_key_for_user(redis, mongo, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongo)
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    user_collection = db["users"]
    key_collection = db["apikeys"]
    assert user_collection.count_documents({}) == 1
    assert key_collection.count_documents({}) == 1
    assert not handler.check_key(newKey) == None
    handler.delete_key_for_user(newKey, "NewUser")
    user = user_collection.find_one({})
    assert user["username"] == "NewUser"
    assert len(user["keys"]) == 0
    # The key will be rettained, only removed from the user.
    # it needs to be retained for quota purposes
    assert key_collection.count_documents({}) == 1
    assert handler.check_key(newKey) == None


def test_delete_key(redis, mongo, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongo)
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    user_collection = db["users"]
    key_collection = db["apikeys"]
    assert user_collection.count_documents({}) == 1
    assert key_collection.count_documents({}) == 1
    assert not handler.check_key(newKey) == None
    handler.delete_key(newKey)
    user = user_collection.find_one({})
    assert user["username"] == "NewUser"
    assert len(user["keys"]) == 0
    assert key_collection.count_documents({}) == 1
    assert handler.check_key(newKey) == None


def test_set_key_activity(redis, mongo, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongo)
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    # Create key
    newKey = handler.create_key("NewUser", "NewKey")
    db = mongo["gateway"]
    user_collection = db["users"]
    key_collection = db["apikeys"]
    # Make sure key is valid at start
    assert not handler.check_key(newKey) == None
    # deactivate key
    handler.set_key_activity(newKey, "NewUser", False)
    key_data = key_collection.find_one({"key": newKey})
    assert key_data["active"] == False
    # Ensure key still exists
    user = user_collection.find_one({"username": "NewUser"})
    assert len(user["keys"]) == 1
    # and key is inactive
    assert not handler.check_key(newKey) == None
    # reactivate and test that the key is now active again
    handler.set_key_activity(newKey, "NewUser", True)
    key_data = key_collection.find_one({"key": newKey})
    assert key_data["active"] == True
    assert not handler.check_key(newKey) == None

from pytest_mock_resources import create_redis_fixture
import mongomock
from app.services.key_service import KeyService
import app.db.mongo
import app.db.redis

redis = create_redis_fixture()


# Testing whether keys are checked correctly
def test_check_key(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    keys = {
        "ABC": '{"user" : "a", "key" : "ABC"}',
        "DEF": '{"user" : "a", "key" : "DEF"}',
    }
    redis.mset(keys)
    assert not handler.get_user_key_if_active("ABC") == None
    assert not handler.get_user_key_if_active("DEF") == None
    assert handler.get_user_key_if_active("BCE") == None


# Testing whether keys are created correctly
def test_create_key(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    newKey = handler.create_key("NewUser", "NewKey")
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    key_collection = db[app.db.mongo.KEY_COLLECTION]
    assert user_collection.count_documents({}) == 1
    user = user_collection.find_one({})
    assert user[app.db.mongo.ID_FIELD] == "NewUser"
    assert len(user["keys"]) == 1
    assert key_collection.count_documents({}) == 1
    assert not handler.get_user_key_if_active(newKey) == None


def test_delete_key_for_user(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    newKey = handler.create_key("NewUser", "NewKey")
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    key_collection = db[app.db.mongo.KEY_COLLECTION]
    assert user_collection.count_documents({}) == 1
    assert key_collection.count_documents({}) == 1
    assert not handler.get_user_key_if_active(newKey) == None
    handler.delete_key_for_user(newKey, "NewUser")
    user = user_collection.find_one({})
    assert user[app.db.mongo.ID_FIELD] == "NewUser"
    assert len(user["keys"]) == 0
    # The key will be rettained, only removed from the user.
    # it needs to be retained for quota purposes
    assert key_collection.count_documents({}) == 1
    assert handler.get_user_key_if_active(newKey) == None


def test_delete_key(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    newKey = handler.create_key("NewUser", "NewKey")
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    key_collection = db[app.db.mongo.KEY_COLLECTION]
    assert user_collection.count_documents({}) == 1
    assert key_collection.count_documents({}) == 1
    assert not handler.get_user_key_if_active(newKey) == None
    handler.delete_key(newKey)
    user = user_collection.find_one({})
    assert user[app.db.mongo.ID_FIELD] == "NewUser"
    assert len(user["keys"]) == 0
    assert key_collection.count_documents({}) == 1
    assert handler.get_user_key_if_active(newKey) == None


def test_set_key_activity(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    # Create key
    newKey = handler.create_key("NewUser", "NewKey")
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    key_collection = db[app.db.mongo.KEY_COLLECTION]
    # Make sure key is valid at start
    assert not handler.get_user_key_if_active(newKey) == None
    # deactivate key
    handler.set_key_activity(newKey, "NewUser", False)
    key_data = key_collection.find_one({"key": newKey})
    assert key_data["active"] == False
    # Ensure key still exists
    user = user_collection.find_one({app.db.mongo.ID_FIELD: "NewUser"})
    assert len(user["keys"]) == 1
    # and key is inactive
    assert handler.get_user_key_if_active(newKey) == None
    # reactivate and test that the key is now active again
    handler.set_key_activity(newKey, "NewUser", True)
    key_data = key_collection.find_one({"key": newKey})
    assert key_data["active"] == True
    assert not handler.get_user_key_if_active(newKey) == None

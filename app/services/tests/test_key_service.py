from pytest_mock_resources import create_redis_fixture
from fastapi import HTTPException
import mongomock
from app.services.key_service import KeyService
from app.services.user_service import UserService
import app.db.mongo
import app.db.redis

from app.models.keys import APIKey
from app.models.user import User

redis = create_redis_fixture()


def create_test_user(username="TestUser"):
    return User(auth_id=username, first_name="Test", last_name="User")


def test_init_keys(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    handler = KeyService()
    # Retrieves the keys from the mongo db
    empty_keys = handler.list_keys()
    assert len(empty_keys) == 0
    key_collection = db[app.db.mongo.KEY_COLLECTION]
    activekey = APIKey(user="A", key="ABCD", active=True, name="Test")
    inactivekey = APIKey(user="B", key="ABC", active=False, name="Test")
    # Add keys to the db.
    key_collection.insert_one(activekey.model_dump())
    key_collection.insert_one(inactivekey.model_dump())
    # Assure, that they don't work yet
    assert handler.get_user_key_if_active("ABCD") == None
    assert handler.get_user_key_if_active("ABC") == None
    handler.init_keys()
    # The active key works now
    key_data = handler.get_user_key_if_active("ABCD")
    assert key_data.user == "A"
    # The inactive still doesn't
    assert handler.get_user_key_if_active("ABC") == None


# Testing whether keys are checked correctly
def test_check_key(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    keys = {
        "ABC": '{"user" : "a", "key" : "ABC", "name" : "TestKey", "active" : true}',
        "DEF": '{"user" : "b", "key" : "DEF", "name" : "TestKey", "active" : true}',
    }
    redis.mset(keys)
    a_key = handler.get_user_key_if_active("ABC")
    assert a_key.user == "a"
    b_key = handler.get_user_key_if_active("DEF")
    assert b_key.user == "b"
    assert handler.get_user_key_if_active("BCE") == None


# Testing whether keys are created correctly
def test_create_key(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    test_user = create_test_user()
    try:
        newKey = handler.create_key(test_user.auth_id, "NewKey")
    except HTTPException as e:
        assert e.status_code == 400
        assert e.detail == "User does not exist"
    user_service = UserService()
    user_service.init_user_db()
    first_user = user_service.create_new_user(test_user)
    second_user = user_service.create_new_user(create_test_user("NewUser"))
    # Check user has no keys yet.
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    user = user_collection.find_one({"auth_id": first_user.auth_id})
    assert len(user["keys"]) == 0
    key1 = handler.create_key(first_user.auth_id, "NewKey")
    user = user_collection.find_one({"auth_id": first_user.auth_id})
    assert len(user["keys"]) == 1
    user = user_collection.find_one({"auth_id": second_user.auth_id})
    assert len(user["keys"]) == 0
    key_collection = db[app.db.mongo.KEY_COLLECTION]
    assert key_collection.count_documents({}) == 1
    assert not handler.get_user_key_if_active(key1.key) == None

    # Test a second key creation works.
    key2 = handler.create_key(first_user.auth_id, "NewKey2")
    user = user_collection.find_one({"auth_id": first_user.auth_id})
    assert len(user["keys"]) == 2
    assert key_collection.count_documents({}) == 2

    # Test a key creation for second user.
    key3 = handler.create_key(second_user.auth_id, "NewKey3")
    user = user_collection.find_one({"auth_id": first_user.auth_id})
    assert len(user["keys"]) == 2
    assert key_collection.count_documents({}) == 3
    user = user_collection.find_one({"auth_id": second_user.auth_id})
    assert len(user["keys"]) == 1

    # Test duplicate key doesn't work
    assert not handler._add_key(key2)
    assert key_collection.count_documents({}) == 3
    user = user_collection.find_one({"auth_id": second_user.auth_id})
    assert len(user["keys"]) == 1


def test_delete_key_for_user(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    user_service = UserService()
    user_service.init_user_db()
    test_user = user_service.create_new_user(create_test_user())
    newKey = handler.create_key(test_user.auth_id, "NewKey")
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    key_collection = db[app.db.mongo.KEY_COLLECTION]
    assert user_collection.count_documents({}) == 1
    assert key_collection.count_documents({}) == 1
    assert not handler.get_user_key_if_active(newKey.key) == None
    handler.delete_key_for_user(newKey.key, test_user.auth_id)
    assert handler.get_user_key_if_active(newKey.key) == None
    user = user_collection.find_one({})
    assert user[app.db.mongo.ID_FIELD] == test_user.auth_id
    assert len(user["keys"]) == 0
    # The key will be rettained, only removed from the user.
    # it needs to be retained for quota purposes
    assert key_collection.count_documents({}) == 1
    assert handler.get_user_key_if_active(newKey.key) == None


def test_delete_key(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    user_service = UserService()
    user_service.init_user_db()
    test_user = user_service.create_new_user(create_test_user())
    newKey = handler.create_key(test_user.auth_id, "NewKey")
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    key_collection = db[app.db.mongo.KEY_COLLECTION]
    assert user_collection.count_documents({}) == 1
    assert key_collection.count_documents({}) == 1
    assert not handler.get_user_key_if_active(newKey.key) == None
    handler.delete_key(newKey.key)
    user = user_collection.find_one({})
    assert user[app.db.mongo.ID_FIELD] == test_user.auth_id
    assert len(user["keys"]) == 0
    assert key_collection.count_documents({}) == 1
    assert handler.get_user_key_if_active(newKey.key) == None


def test_set_key_activity(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    handler = KeyService()
    handler.init_keys()
    user_service = UserService()
    user_service.init_user_db()
    test_user = user_service.create_new_user(create_test_user())
    # Create key
    newKey = handler.create_key(test_user.auth_id, "NewKey")
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    key_collection = db[app.db.mongo.KEY_COLLECTION]
    # Make sure key is valid at start
    assert not handler.get_user_key_if_active(newKey.key) == None
    # deactivate key
    handler.set_key_activity(newKey, False)
    key_data = key_collection.find_one({"key": newKey.key})
    assert key_data["active"] == False
    # Ensure key still exists
    user = user_collection.find_one({app.db.mongo.ID_FIELD: test_user.auth_id})
    assert len(user["keys"]) == 1
    # and key is inactive
    assert handler.get_user_key_if_active(newKey.key) == None
    # reactivate and test that the key is now active again
    handler.set_key_activity(newKey, True)
    key_data = key_collection.find_one({"key": newKey.key})
    assert key_data["active"] == True
    assert not handler.get_user_key_if_active(newKey.key) == None

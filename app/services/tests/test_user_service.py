from pytest_mock_resources import create_redis_fixture
import mongomock
from app.services.key_service import KeyService
from app.services.user_service import UserService
import app.db.mongo
import app.db.redis
from app.models.user import User

redis = create_redis_fixture()


def createTestSessionData(user: str, groups: list = ["test"]):
    return {
        "auth_name": user,
        "first_name": "test",
        "last_name": "test",
        "auth_groups": groups,
    }


def create_test_user(user: str = "TestUser") -> User:
    return User(auth_id=user, first_name="test", last_name="test")


# Testing whether keys are checked correctly
def test_create_user(monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    user_service = UserService()
    user_service.init_user_db()
    user_service.create_new_user(create_test_user("Test"))
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    assert user_collection.count_documents({}) == 1
    user = user_service.get_user_by_id("Test")
    assert user.first_name == "test"
    assert user.last_name == "test"
    assert not user.admin


def test_no_duplicate_user(monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    user_service = UserService()
    user_service.init_user_db()
    test_user = create_test_user("Test")
    created_user = user_service.get_or_create_user_from_auth_data(
        auth_id=test_user.auth_id,
        first_name=test_user.first_name,
        last_name=test_user.last_name,
    )
    assert created_user.first_name == "test"
    assert created_user.last_name == "test"
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    user_collection = db[app.db.mongo.USER_COLLECTION]
    assert user_collection.count_documents({}) == 1
    next_created_user = user_service.get_or_create_user_from_auth_data(
        auth_id=test_user.auth_id,
        first_name=test_user.first_name,
        last_name=test_user.last_name,
    )
    # Nothing new.
    assert user_collection.count_documents({}) == 1
    created_user = user_service.create_new_user(test_user)
    assert created_user == None
    assert user_collection.count_documents({}) == 1


def test_reset_user(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    key_service = KeyService()
    key_service.init_keys()
    test_user: User = create_test_user()
    user_service = UserService()
    user_service.init_user_db()
    created_user = user_service.get_or_create_user_from_auth_data(
        auth_id=test_user.auth_id,
        first_name=test_user.first_name,
        last_name=test_user.last_name,
    )
    # create 2 keys
    key1 = key_service.create_key(created_user.auth_id, "Key1")
    key2 = key_service.create_key(created_user.auth_id, "Key2")
    # deactivate one key
    key_service.delete_key_for_user(key1, created_user.auth_id)
    user_service.update_agreement_version(created_user.auth_id, "2.0")
    user = user_service.get_user_by_id(created_user.auth_id)
    assert user.seen_guide_version == "2.0"
    # reset
    reset_user = user_service.reset_user(created_user)
    user = user_service.get_user_by_id(created_user.auth_id)
    assert user.seen_guide_version == ""
    assert len(user.keys) == 1
    assert key2 in user.keys
    assert key1 not in user.keys

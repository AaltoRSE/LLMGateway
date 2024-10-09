import mongomock
from app.services.session_service import SessionService
from app.services.user_service import UserService
from fastapi import HTTPException
import app.db.mongo
from app.models.user import User


def createTestSessionData(user: str, groups: list = ["test"]):
    return {
        "auth_name": user,
        "first_name": "test",
        "last_name": "test",
        "auth_groups": groups,
    }


def getTestUser(user: str) -> User:
    return User(auth_id=user, first_name="test", last_name="test")


# Testing whether keys are checked correctly
def test_create_user(monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    user_service = UserService()
    user_service.init_user_db()
    user_service.create_new_user(getTestUser("Test"))
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
    test_user = getTestUser("Test")
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

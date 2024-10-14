from pytest_mock_resources import create_redis_fixture
from app.services.session_service import SessionService
from app.services.user_service import UserService
from fastapi import HTTPException
import app.db.redis
import app.db.mongo
import mongomock
import time


redis = create_redis_fixture()


def createTestSessionData(user: str, groups: list = ["test"]):
    return {
        "auth_name": user,
        "first_name": "test",
        "last_name": "test",
        "auth_groups": groups,
        "email": "",
        "agreement_ok": True,
    }


# Testing whether keys are checked correctly
def test_create_session(redis, monkeypatch):
    monkeypatch.setattr(app.db.redis, "redis_session_client", redis)
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    session_service = SessionService()
    user_service = UserService()
    session = session_service.create_session(
        session_data=createTestSessionData(user="Test"),
        source_ip="Foo",
        user_service=user_service,
    )
    users = user_service.get_all_users()
    assert len(users) == 1
    assert users[0].auth_id == "Test"
    session2 = session_service.get_session(session_key=session.key)
    assert session2.user == session.user
    assert session2.ip == session.ip


def test_expire_session(redis, monkeypatch):
    monkeypatch.setattr(app.db.redis, "redis_session_client", redis)
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    session_service = SessionService(exp_time=1)
    user_service = UserService()
    session = session_service.create_session(
        session_data=createTestSessionData(user="Test"),
        source_ip="Foo",
        user_service=user_service,
    )
    time.sleep(2)
    # Should have expired immediately
    assert session_service.get_session(session.key) == None


def test_delete_session(redis, monkeypatch):
    monkeypatch.setattr(app.db.redis, "redis_session_client", redis)
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    session_service = SessionService()
    user_service = UserService()
    session = session_service.create_session(
        session_data=createTestSessionData(user="Test"),
        source_ip="Foo",
        user_service=user_service,
    )
    session_service.delete_session(session.key)
    assert session_service.get_session(session.key) == None
    users = user_service.get_all_users()
    assert len(users) == 1

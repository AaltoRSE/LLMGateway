import time
from fastapi import HTTPException
import pytest

from app.services.session_service import SessionService
from app.services.user_service import UserService
from app.schemas.user_schema import SessionAuthData
from app.dbs.redis.redis import get_session_client


def createTestSessionData(auth_id: str, groups: list = ["test"]) -> SessionAuthData:
    return SessionAuthData(
        auth_id=auth_id, first_name="test", last_name="test", roles=groups
    )


# Testing whether keys are checked correctly
@pytest.mark.asyncio
async def test_create_session(
    session_service: SessionService, user_service: UserService
):
    session = await session_service.create_session(
        session_data=createTestSessionData(auth_id="TestUser", groups=["employee"]),
        source_ip="Foo",
        user_service=user_service,
    )
    # Check, that a user was created
    users = await user_service.get_all_users()
    assert len(users) == 1
    assert users[0].auth_id == "TestUser"
    session2 = await session_service.get_session(session_key=session.key)
    assert session2.user_id == session.user_id
    assert session2.ip == session.ip


@pytest.mark.asyncio
async def test_expire_session(user_service, redis_session_client, redis_dbs):
    # We need a different client, that sets a different expiration time.
    session_service = SessionService(redis_session_client, exp_time=1)
    session = await session_service.create_session(
        session_data=createTestSessionData(auth_id="Test", groups=["employee"]),
        source_ip="Foo",
        user_service=user_service,
    )
    time.sleep(2)
    # Should have expired immediately
    assert await session_service.get_session(session.key) is None


@pytest.mark.asyncio
async def test_delete_session(
    session_service: SessionService, user_service: UserService
):
    session = await session_service.create_session(
        session_data=createTestSessionData(auth_id="Test", groups=["employee"]),
        source_ip="Foo",
        user_service=user_service,
    )
    await session_service.delete_session(session.key)
    assert await session_service.get_session(session.key) is None
    users = await user_service.get_all_users()
    assert len(users) == 1

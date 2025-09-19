from datetime import datetime
import pytest


from app.services.balance_service import BalanceService
from app.services.usage_service import UsageService
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.schemas.user_schema import User, UserBase
from app.schemas.key_schema import APIKey
from app.schemas.usage_schema import APIRequest, RequestSource


def create_test_entry(
    collection, key="testkey", user="testUser", model="testModel", timestamp=None
):
    if not timestamp:
        timestamp = datetime.fromtimestamp(0)
    else:
        timestamp = datetime.fromtimestamp(timestamp)
    collection.insert_one(
        {
            "user": user,
            "model": model,
            "prompt_tokens": 10,
            "completion_tokens": 11,
            "cost": 1.1,
            "key": key,
            "timestamp": timestamp,
        }
    )


# Testing whether keys are checked correctly
@pytest.mark.asyncio
async def test_log_usage(
    usage_service: UsageService,
    key_service: KeyService,
    normal_user: User,
    admin_user: User,
):
    await key_service.init_keys()
    key1 = await key_service.create_key(user_id=normal_user.id, name="Key1")
    key2 = await key_service.create_key(user_id=admin_user.id, name="Key2")
    key3 = await key_service.create_key(name="Key3", service="TestService")
    request1 = APIRequest(
        prompt_tokens=10,
        completion_tokens=10,
        cost=0.4,
        model="testModel",
        timestamp=datetime.now(),
    )
    request2 = APIRequest(
        prompt_tokens=5,
        completion_tokens=5,
        cost=1.0,
        model="testModel2",
        timestamp=datetime.now(),
    )
    source1 = RequestSource(key=key1.key, user_id=normal_user.id)
    source2 = RequestSource(key=key2.key, user_id=admin_user.id)
    source3 = RequestSource(key=key3.key)
    await usage_service.log_usage(source1, request1)
    await usage_service.log_usage(source2, request2)
    await usage_service.log_usage(source1, request2)
    await usage_service.log_usage(source3, request2)
    key1_balance = await usage_service.get_current_key_balance(key1.key)
    key2_balance = await usage_service.get_current_key_balance(key2.key)
    key3_balance = await usage_service.get_current_key_balance(key3.key)
    user1_balance = await usage_service.get_current_user_balance(normal_user.id)
    user2_balance = await usage_service.get_current_user_balance(admin_user.id)
    assert key1_balance.balance_used == pytest.approx(1.4)
    assert key2_balance.balance_used == pytest.approx(1.0)
    assert key3_balance.balance_used == pytest.approx(1.0)
    assert user1_balance.balance_used == pytest.approx(1.4)
    assert user2_balance.balance_used == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_get_usage_for_user(
    usage_service: UsageService,
    key_service: KeyService,
    normal_user: User,
    admin_user: User,
):
    key_service.init_keys()
    key1 = await key_service.create_key(user_id=normal_user.id, name="Key1")
    key2 = await key_service.create_key(user_id=admin_user.id, name="Key3")
    request1 = APIRequest(
        prompt_tokens=10,
        completion_tokens=10,
        cost=0.4,
        model="testModel",
        timestamp=datetime.now(),
    )
    request2 = APIRequest(
        prompt_tokens=5,
        completion_tokens=5,
        cost=1.0,
        model="testModel2",
        timestamp=datetime.now(),
    )
    source1 = RequestSource(key=key1.key, user_id=normal_user.id)
    source2 = RequestSource(key=key2.key, user_id=admin_user.id)
    await usage_service.log_usage(source1, request1)
    await usage_service.log_usage(source1, request2)
    await usage_service.log_usage(source2, request2)
    usage = await usage_service.get_usage_for_user(normal_user.id)
    assert len(usage) == 2

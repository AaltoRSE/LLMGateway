from app.services.quota_service import QuotaService
from app.services.usage_service import UsageService
from app.services.key_service import KeyService
from app.services.user_service import UserService
import mongomock
from app.models.user import User
from app.models.keys import APIKey
from app.models.quota import (
    RequestUsage,
    UsagePerKeyForUser,
    KeyPerModelUsage,
    ModelUsage,
    TimedKeyQuota,
    TimedUserQuota,
)
import app.db.mongo
import app.db.redis
from datetime import datetime
import pytest


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
def test_quota_update(monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())

    usage_service = UsageService()
    quota_service = QuotaService(usage_service=usage_service)
    user_service = UserService()
    user_service.init_user_db()
    key_service = KeyService()
    print(f"Keys at the beginning : {key_service.list_keys()}")
    key_service.init_keys()
    test_user = User(auth_id="DEF", first_name="Test", last_name="User")
    user_service.create_new_user(test_user)
    user = "DEF"
    key1 = key_service.create_key(user=user, name="Key1")
    key2 = key_service.create_key(user=user, name="Key2")
    print(f"Keys after creation: {key_service.list_keys()}")
    user_key = APIKey(key=key1.key, user=key1.user, name="Key1", active=True)
    user_key2 = APIKey(key=key2.key, user=key2.user, name="Key2", active=True)
    model1 = "testmodel"
    model2 = "testmodel2"
    quota = RequestUsage(
        prompt_tokens=10, completion_tokens=11, prompt_cost=1, completion_cost=1
    )
    quota_service.add_usage(user_key, model1, quota)
    quota_service.add_usage(user_key, model1, quota)
    quota_service.add_usage(user_key2, model1, quota)
    quota_service.add_usage(user_key, model2, quota)
    quota_service.add_usage(user_key2, model2, quota)
    usage: UsagePerKeyForUser = usage_service.get_usage_per_key_for_user(user=user)
    assert len(usage.keys) == 2
    key1_data: KeyPerModelUsage = usage.keys[0]
    key2_data: KeyPerModelUsage = usage.keys[1]
    if key2_data.key == user_key.key:
        temp = key2_data
        key2_data = key1_data
        key1_data = temp
    assert key1_data.prompt_tokens == 30
    assert key1_data.completion_tokens == 33
    assert key2_data.prompt_tokens == 20
    assert key2_data.completion_tokens == 22


def test_get_usage_per_model(monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    # We need all the services unfortunately
    usage_service = UsageService()
    quota_service = QuotaService(usage_service=usage_service)
    user_service = UserService()
    user_service.init_user_db()
    key_service = KeyService()
    print(f"Keys at the beginning : {key_service.list_keys()}")
    key_service.init_keys()
    test_user = User(auth_id="DEF", first_name="Test", last_name="User")
    user_service.create_new_user(test_user)
    user = "DEF"
    key1 = key_service.create_key(user=user, name="Key1")
    key2 = key_service.create_key(user=user, name="Key2")
    print(f"Keys after creation: {key_service.list_keys()}")
    user_key = APIKey(key=key1.key, user=user, name="Key1", active=True)
    user_key2 = APIKey(key=key2.key, user=user, name="Key2", active=True)
    model1 = "testmodel"
    model2 = "testmodel2"
    quota = RequestUsage(
        prompt_tokens=10, completion_tokens=11, prompt_cost=1, completion_cost=1
    )
    quota_service.add_usage(user_key, model1, quota)
    quota_service.add_usage(user_key, model1, quota)
    quota_service.add_usage(user_key2, model1, quota)
    quota_service.add_usage(user_key, model2, quota)
    quota_service.add_usage(user_key2, model2, quota)
    usage = usage_service._get_usage_per_model()
    assert len(usage) == 2
    model1_data: ModelUsage = usage[0]
    model2_data: ModelUsage = usage[1]
    if model2_data.model == model1:
        temp = model2_data
        model2_data = model1_data
        model1_data = temp

    assert model1_data.usage.prompt_tokens == 30
    assert model1_data.usage.completion_tokens == 33
    assert model1_data.usage.cost == 63
    assert model2_data.usage.prompt_tokens == 20
    assert model2_data.usage.completion_tokens == 22
    assert model2_data.usage.cost == 42


def test_mongo_db_retrieval(monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    # We need all the services unfortunately
    usage_service = UsageService()
    quota_service = QuotaService(usage_service=usage_service)

    user_service = UserService()
    user_service.init_user_db()
    key_service = KeyService()
    print(f"Keys at the beginning : {key_service.list_keys()}")
    key_service.init_keys()
    test_user = User(auth_id="DEF", first_name="Test", last_name="User")
    test_user2 = User(auth_id="ABC", first_name="Test", last_name="User")
    user_service.create_new_user(test_user)
    user_service.create_new_user(test_user2)
    key1 = key_service.create_key(user=test_user.auth_id, name="Key1")
    key2 = key_service.create_key(user=test_user2.auth_id, name="Key2")
    print(f"Keys after creation: {key_service.list_keys()}")
    user_key = APIKey(key=key1.key, user=test_user.auth_id, name="Key1", active=True)
    user_key2 = APIKey(key=key2.key, user=test_user2.auth_id, name="Key2", active=True)
    model1 = "testmodel"
    model2 = "testmodel2"
    quota = RequestUsage(
        prompt_tokens=10, completion_tokens=11, prompt_cost=1, completion_cost=1
    )
    quota_service.add_usage(user_key, model1, quota)
    quota_service.add_usage(user_key, model1, quota)
    quota_service.add_usage(user_key2, model1, quota)
    quota_service.add_usage(user_key, model2, quota)
    quota_service.add_usage(user_key2, model2, quota)

    # Now, we clean the redis DBs.
    app.db.redis.redis_key_quota_day_client.flushall()
    app.db.redis.redis_key_quota_week_client.flushall()
    app.db.redis.redis_user_quota_day_client.flushall()
    app.db.redis.redis_user_quota_week_client.flushall()

    # Now, we make sure the data is not in redis
    assert quota_service.user_week_db.get(user_key.user) == None
    assert quota_service.key_week_db.get(user_key.key) == None
    assert quota_service.user_day_db.get(user_key.user) == None
    assert quota_service.key_day_db.get(user_key.key) == None

    user1_quota: TimedUserQuota = quota_service.get_user_quotas(user=user_key.user)
    user2_quota: TimedUserQuota = quota_service.get_user_quotas(user=user_key2.user)
    assert user1_quota.week_quota.usage.prompt_tokens == 30
    assert user1_quota.week_quota.usage.completion_tokens == 33
    assert user2_quota.week_quota.usage.prompt_tokens == 20
    assert user2_quota.week_quota.usage.completion_tokens == 22
    assert user1_quota.day_quota.usage.prompt_tokens == 30
    assert user1_quota.day_quota.usage.completion_tokens == 33
    assert user2_quota.day_quota.usage.prompt_tokens == 20
    assert user2_quota.day_quota.usage.completion_tokens == 22

    key1_quota: TimedKeyQuota = quota_service.get_key_quotas(key=user_key.key)
    key2_quota: TimedKeyQuota = quota_service.get_key_quotas(key=user_key2.key)
    assert key1_quota.week_quota.usage.prompt_tokens == 30
    assert key1_quota.week_quota.usage.completion_tokens == 33
    assert key2_quota.week_quota.usage.prompt_tokens == 20
    assert key2_quota.week_quota.usage.completion_tokens == 22
    assert key1_quota.day_quota.usage.prompt_tokens == 30
    assert key1_quota.day_quota.usage.completion_tokens == 33
    assert key2_quota.day_quota.usage.prompt_tokens == 20
    assert key2_quota.day_quota.usage.completion_tokens == 22


def test_per_hour_usages(monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    usage_service = UsageService()
    create_test_entry(usage_service.usage_collection, timestamp=4000)
    create_test_entry(usage_service.usage_collection, timestamp=8000)
    create_test_entry(usage_service.usage_collection, timestamp=12000)
    create_test_entry(usage_service.usage_collection, timestamp=4000)
    create_test_entry(usage_service.usage_collection, user="NewUser", timestamp=4000)
    create_test_entry(usage_service.usage_collection, model="NewModel", timestamp=8000)
    model_usage = usage_service.get_usage_per_model_per_hour()
    assert len(model_usage) == 2
    new_model_usage = model_usage[0]
    test_model_usage = model_usage[1]
    if not new_model_usage.model == "NewModel":
        new_model_usage = model_usage[1]
        test_model_usage = model_usage[0]
    assert len(new_model_usage.usage) == 1
    assert len(test_model_usage.usage) == 3
    assert new_model_usage.cost == pytest.approx(1.1, rel=1e-4)
    assert test_model_usage.cost == pytest.approx(5.5, rel=1e-4)

    user_usage = usage_service.get_usage_per_user_per_hour()
    assert len(user_usage) == 2
    new_user_usage = user_usage[0]
    test_user_usage = user_usage[1]
    if not new_user_usage.user == "NewUser":
        new_user_usage = user_usage[1]
        test_user_usage = user_usage[0]
    assert len(new_user_usage.usage) == 1
    assert len(test_user_usage.usage) == 3
    assert new_user_usage.cost == pytest.approx(1.1, rel=1e-4)
    assert test_user_usage.cost == pytest.approx(5.5, rel=1e-4)

    new_model_usage2 = usage_service.get_usage_over_time_for_model("NewModel")
    assert len(new_model_usage2) == 1
    assert new_model_usage2[0].cost == pytest.approx(1.1, rel=1e-4)
    test_model_usage2 = usage_service.get_usage_over_time_for_model("testModel")
    assert len(test_model_usage2) == 3
    assert test_model_usage2[0].cost == pytest.approx(3.3, rel=1e-4)
    assert test_model_usage2[1].cost == pytest.approx(1.1, rel=1e-4)
    assert test_model_usage2[2].cost == pytest.approx(1.1, rel=1e-4)

    new_user_usage2 = usage_service.get_usage_over_time_for_user("NewUser")
    assert len(new_user_usage2) == 1
    assert new_user_usage2[0].cost == pytest.approx(1.1, rel=1e-4)
    test_user_usage2 = usage_service.get_usage_over_time_for_user("testUser")
    assert len(test_user_usage2) == 3
    assert test_user_usage2[0].cost == pytest.approx(2.2, rel=1e-4)
    assert test_user_usage2[1].cost == pytest.approx(2.2, rel=1e-4)
    assert test_user_usage2[2].cost == pytest.approx(1.1, rel=1e-4)

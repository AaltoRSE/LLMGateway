from pytest_mock_resources import create_redis_fixture
from app.services.quota_service import QuotaService
from app.services.usage_service import UsageService
from app.services.key_service import KeyService
from app.services.user_service import UserService
import mongomock
from app.models.user import User
from app.models.keys import UserKey
from app.models.quota import RequestQuota, UsagePerKeyForUser, KeyPerModelUsage
import app.db.mongo
import app.db.redis


redis = create_redis_fixture()


# Testing whether keys are checked correctly
def test_quota_update(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    # NOTE: We use the same redis here. They should not overlap,
    # since key and user are different, and those are the entries in this service.
    monkeypatch.setattr(app.db.redis, "redis_usage_user_client", redis)
    monkeypatch.setattr(app.db.redis, "redis_usage_key_client", redis)
    monkeypatch.setattr(app.db.redis, "redis_key_client", redis)
    quota_service = QuotaService()
    usage_service = UsageService()
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
    user_key = UserKey(key=key1, user=user)
    user_key2 = UserKey(key=key2, user=user)
    model1 = "testmodel"
    model2 = "testmodel2"
    quota = RequestQuota(
        prompt_tokens=10, completion_tokens=11, prompt_cost=1, completion_cost=1
    )
    quota_service.update_quota(user_key, model1, quota)
    quota_service.update_quota(user_key, model1, quota)
    quota_service.update_quota(user_key2, model1, quota)
    quota_service.update_quota(user_key, model2, quota)
    quota_service.update_quota(user_key2, model2, quota)
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

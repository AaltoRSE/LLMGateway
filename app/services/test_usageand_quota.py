from pytest_mock_resources import create_redis_fixture
from pytest_mock_resources import create_mongo_fixture
from app.services.quota_service import QuotaService
from app.services.usage_service import UsageService
from app.models.keys import UserKey
from app.models.quota import RequestQuota, UsagePerKeyForUser, KeyPerModelUsage
import app.db.mongo
import app.db.redis

redis = create_redis_fixture()
mongo = create_mongo_fixture()


# Testing whether keys are checked correctly
def test_check_key(redis, mongo, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongo)
    # NOTE: We use the same redis here. They should not overlap,
    # since key and user are different, and those are the entries in this service.
    monkeypatch.setattr(app.db.redis, "redis_usage_user_client", redis)
    monkeypatch.setattr(app.db.redis, "redis_usage_key_client", redis)
    quota_service = QuotaService()
    usage_service = UsageService()
    user_key = UserKey(key="ABC", user="DEF")
    user_key2 = UserKey(key="ABCD", user="DEF")
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
    usage: UsagePerKeyForUser = usage_service.get_usage_per_key_for_user(user="DEF")
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

from pytest_mock_resources import create_redis_fixture
from pytest_mock_resources import create_mongo_fixture
from key_handler import key_handler

redis = create_redis_fixture()
mongo = create_mongo_fixture()


def test_check_key(redis, mongo):
    handler = key_handler(True)
    handler.setup(mongo, redis)
    keys = ["ABC", "DEF"]
    redis.sadd("keys", *keys)
    assert handler.check_key("ABC") == True
    assert handler.check_key("DEF") == True
    assert handler.check_key("BCE") == False

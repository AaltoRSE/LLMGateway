from pytest_mock_resources import create_mongo_fixture
from logging_handler import logging_handler

mongo = create_mongo_fixture()


def test_log_usage_for_key(mongo):
    handler = logging_handler(True)
    handler.setup(mongo)
    db = mongo["gateway"]
    logCollection = db["logs"]
    handler.log_usage_for_key(50, "newModel", "123")
    assert logCollection.count_documents({}) == 1
    handler.log_usage_for_key(70, "model2", "123")
    assert logCollection.count_documents({}) == 2
    handler.log_usage_for_key(50, "model2", "321")
    assert logCollection.count_documents({"model": "model2"}) == 2
    assert logCollection.count_documents({"source": "123"}) == 2
    assert logCollection.count_documents({"source": "321"}) == 1
    assert logCollection.count_documents({"sourcetype": "apikey"}) == 3
    firstLog = logCollection.find_one({"model": "newModel"})
    secondLog = logCollection.find_one({"tokencount": 70})
    assert firstLog["timestamp"] <= secondLog["timestamp"]


def test_log_usage_for_user(mongo):
    handler = logging_handler(True)
    handler.setup(mongo)
    db = mongo["gateway"]
    logCollection = db["logs"]
    handler.log_usage_for_user(50, "newModel", "123")
    assert logCollection.count_documents({}) == 1
    handler.log_usage_for_user(70, "model2", "123")
    assert logCollection.count_documents({}) == 2
    handler.log_usage_for_user(50, "model2", "321")
    assert logCollection.count_documents({"model": "model2"}) == 2
    assert logCollection.count_documents({"source": "123"}) == 2
    assert logCollection.count_documents({"source": "321"}) == 1
    assert logCollection.count_documents({"sourcetype": "user"}) == 3
    firstLog = logCollection.find_one({"model": "newModel"})
    secondLog = logCollection.find_one({"tokencount": 70})
    assert firstLog["timestamp"] <= secondLog["timestamp"]

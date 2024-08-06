from pytest_mock_resources import create_mongo_fixture
from gateway.app.logging.logging_handler import LoggingHandler

mongo = create_mongo_fixture()


def test_log_usage_for_key(mongo):
    handler = LoggingHandler(True)
    handler.setup(mongo)
    db = mongo["gateway"]
    log_collection = db["logs"]
    handler.log_usage_for_key(50, "newModel", "123")
    assert log_collection.count_documents({}) == 1
    handler.log_usage_for_key(70, "model2", "123")
    assert log_collection.count_documents({}) == 2
    handler.log_usage_for_key(50, "model2", "321")
    assert log_collection.count_documents({"model": "model2"}) == 2
    assert log_collection.count_documents({"source": "123"}) == 2
    assert log_collection.count_documents({"source": "321"}) == 1
    assert log_collection.count_documents({"sourcetype": "apikey"}) == 3
    first_log = log_collection.find_one({"model": "newModel"})
    second_log = log_collection.find_one({"tokencount": 70})
    assert first_log["timestamp"] <= second_log["timestamp"]


def test_log_usage_for_user(mongo):
    handler = LoggingHandler(True)
    handler.setup(mongo)
    db = mongo["gateway"]
    log_collection = db["logs"]
    handler.log_usage_for_user(50, "newModel", "123")
    assert log_collection.count_documents({}) == 1
    handler.log_usage_for_user(70, "model2", "123")
    assert log_collection.count_documents({}) == 2
    handler.log_usage_for_user(50, "model2", "321")
    assert log_collection.count_documents({"model": "model2"}) == 2
    assert log_collection.count_documents({"source": "123"}) == 2
    assert log_collection.count_documents({"source": "321"}) == 1
    assert log_collection.count_documents({"sourcetype": "user"}) == 3
    first_log = log_collection.find_one({"model": "newModel"})
    second_log = log_collection.find_one({"tokencount": 70})
    assert first_log["timestamp"] <= second_log["timestamp"]

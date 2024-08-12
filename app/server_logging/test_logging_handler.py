from pytest_mock_resources import create_mongo_fixture
from server_logging.logging_handler import LoggingHandler

mongo = create_mongo_fixture()


def add_test_key(db, key, name="testing", user="test"):
    key_collection = db["apikeys"]
    key_collection.insert_one({"user": user, "active": True, "key": key, "name": name})


def test_log_usage_for_key(mongo):
    handler = LoggingHandler(True)
    db = mongo
    handler.setup(db)
    log_collection = db["logs"]
    add_test_key(db, "123")
    add_test_key(db, "321")
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
    second_log = log_collection.find_one({"completion_tokens": 70})
    assert first_log["timestamp"] <= second_log["timestamp"]


def test_log_usage_for_user(mongo):
    handler = LoggingHandler(True)
    db = mongo
    handler.setup(db)
    log_collection = db["logs"]
    add_test_key(db, "123")
    add_test_key(db, "321")
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
    second_log = log_collection.find_one({"completion_tokens": 70})
    assert first_log["timestamp"] <= second_log["timestamp"]


def test_prompt_vs_completion_logging(mongo):
    handler = LoggingHandler(True)
    db = mongo
    handler.setup(db)
    log_collection = db["logs"]
    add_test_key(db, "123")
    add_test_key(db, "321")
    # Assert we start with a blank sheet
    assert log_collection.count_documents({}) == 0
    handler.log_usage_for_key(80, "newModel", "123")
    handler.log_usage_for_key(70, "model2", "321", 80)
    handler.log_usage_for_key(20, "model2", "321", 90)

    res = handler.get_usage_for_keys("321")
    assert res[0]["usage"]["prompt_tokens"] == 170
    assert res[0]["usage"]["completion_tokens"] == 90

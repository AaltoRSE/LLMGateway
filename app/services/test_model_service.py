from pytest_mock_resources import create_redis_fixture
from pytest_mock_resources import create_mongo_fixture
import app.db.mongo
import app.db.redis
import app
from app.services.model_service import ModelService


redis = create_redis_fixture()
mongo = create_mongo_fixture()


# Testing whether keys are checked correctly
def test_add_model(mongo, redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongo)
    monkeypatch.setattr(app.db.redis, "redis_model_client", redis)
    handler = ModelService()
    handler.init_models()
    currentModels = handler.get_models()
    db = mongo["gateway"]
    model_collection = db["model"]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    handler.add_model(model="test", path="test2", owner="test3")
    # Adding model works
    assert model_collection.count_documents({}) == 1
    failed = False
    try:
        handler.add_model(model="test", path="test2", owner="test3")
    except KeyError as e:
        failed = True
    assert failed
    handler.add_model(model="test2", path="test2", owner="test3")
    # Adding second model works
    assert model_collection.count_documents({}) == 2


def test_model_path_and_get(mongo, redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongo)
    monkeypatch.setattr(app.db.redis, "redis_model_client", redis)
    handler = ModelService()
    handler.init_models()
    currentModels = handler.get_models()
    db = mongo["gateway"]
    model_collection = db["model"]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    handler.add_model(model="test", path="test2", owner="test3")
    assert model_collection.count_documents({}) == 1
    handler.add_model(model="test2", path="test2", owner="test4")
    models = handler.get_models()
    assert len(models) == 2
    found1 = False
    found2 = False
    for model in models:
        if model.id == "test":
            found1 = True
            assert model.owned_by == "test3"
            assert len(model.permissions) == 0
            assert model.object == "model"
        if model.id == "test2":
            found2 = True
            assert model.owned_by == "test4"
            assert len(model.permissions) == 0
            assert model.object == "model"

    assert found1 and found2
    handler.add_model(model="test3", path="test3", owner="test3")
    assert model_collection.count_documents({}) == 3
    assert handler.get_model_path("test") == "test2"
    assert handler.get_model_path("test2") == "test2"
    assert handler.get_model_path("test3") == "test3"
    models = handler.get_models()
    assert len(models) == 3


def test_remove_model(mongo, redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongo)
    monkeypatch.setattr(app.db.redis, "redis_model_client", redis)
    handler = ModelService()
    handler.init_models()
    currentModels = handler.get_models()
    db = mongo["gateway"]
    model_collection = db["model"]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    handler.add_model(model="test", path="test2", owner="test3")

    handler.add_model(model="test2", path="test2", owner="test4")
    handler.remove_model(model="test2")
    assert len(handler.get_models()) == 1
    assert model_collection.count_documents({}) == 1
    assert model_collection.count_documents({"model.id": "test2"}) == 0
    assert model_collection.count_documents({"model.id": "test"}) == 1

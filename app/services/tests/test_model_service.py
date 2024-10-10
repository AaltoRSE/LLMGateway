from pytest_mock_resources import create_redis_fixture
import mongomock
import app.db.mongo
import app.db.redis
from app.services.model_service import ModelService
from app.models.model import LLMModel, LLMModelData
from fastapi import HTTPException

redis = create_redis_fixture()


def create_test_model():
    return LLMModel(path="test", model=LLMModelData(id="test", owned_by="test3"))


def test_init_models(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_model_client", redis)
    handler = ModelService()
    testmodel = create_test_model()
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    model_collection = db[app.db.mongo.MODEL_COLLECTION]
    model_collection.insert_one(testmodel.model_dump())
    try:
        handler.get_model_path(testmodel.model.id)
        assert False, "Model should not have been found without init"
    except HTTPException as e:
        assert e.status_code == 404
        assert e.detail == "Model not found"
    models = handler.get_models()
    # We have one in the db.
    assert len(models) == 1
    handler.init_models()
    path = handler.get_model_path(testmodel.model.id)
    assert path == testmodel.path


# Testing whether keys are checked correctly
def test_add_model(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_model_client", redis)
    handler = ModelService()
    handler.init_models()
    currentModels = handler.get_models()
    db = app.db.mongo.mongo_client[app.db.mongo.DB_NAME]
    model_collection = db[app.db.mongo.MODEL_COLLECTION]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    model = LLMModel(path="test", model=LLMModelData(id="test", owned_by="test3"))
    handler.add_model(model)
    # Adding model works
    assert model_collection.count_documents({}) == 1
    try:
        model = LLMModel(path="test2", model=LLMModelData(id="test", owned_by="test3"))
        handler.add_model(model)
        assert False, "Model should be rejected because the ID already exists"
    except HTTPException as e:
        assert e.status_code == 409
        assert e.detail == "Model already exists"
    model = LLMModel(path="test2", model=LLMModelData(id="test2", owned_by="test3"))
    handler.add_model(model)
    # Adding second model works
    assert model_collection.count_documents({}) == 2


def test_get_model_path(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_model_client", redis)
    handler = ModelService()
    handler.init_models()
    currentModels = handler.get_models()
    db = app.db.mongo.mongo_client["gateway"]
    model_collection = db["model"]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    model = LLMModel(path="test2", model=LLMModelData(id="test", owned_by="test3"))
    handler.add_model(model)
    assert model_collection.count_documents({}) == 1
    model = LLMModel(path="test2", model=LLMModelData(id="test2", owned_by="test4"))
    handler.add_model(model)
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
    model = LLMModel(path="test3", model=LLMModelData(id="test3", owned_by="test3"))
    handler.add_model(model)
    assert model_collection.count_documents({}) == 3
    assert handler.get_model_path("test") == "test2"
    assert handler.get_model_path("test2") == "test2"
    assert handler.get_model_path("test3") == "test3"
    models = handler.get_models()
    assert len(models) == 3


def test_get_model(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_model_client", redis)
    handler = ModelService()
    handler.init_models()
    currentModels = handler.get_models()
    db = app.db.mongo.mongo_client["gateway"]
    model_collection = db["model"]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    model1 = LLMModel(path="test2", model=LLMModelData(id="test", owned_by="test3"))
    handler.add_model(model1)
    assert model_collection.count_documents({}) == 1
    model2 = LLMModel(path="test2", model=LLMModelData(id="test2", owned_by="test4"))
    handler.add_model(model2)
    model1_retrieved = handler.get_model(model1.model.id)
    assert model1_retrieved.model.owned_by == "test3"
    assert model1_retrieved.path == model1.path

    model2_retrieved = handler.get_model(model2.model.id)
    assert model2_retrieved.model.owned_by == "test4"
    assert model2_retrieved.path == model2.path


def test_remove_model(redis, monkeypatch):
    monkeypatch.setattr(app.db.mongo, "mongo_client", mongomock.MongoClient())
    monkeypatch.setattr(app.db.redis, "redis_model_client", redis)
    handler = ModelService()
    handler.init_models()
    currentModels = handler.get_models()
    db = app.db.mongo.mongo_client["gateway"]
    model_collection = db["model"]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    model = LLMModel(path="test2", model=LLMModelData(id="test", owned_by="test3"))
    handler.add_model(model)
    model = LLMModel(path="test2", model=LLMModelData(id="test2", owned_by="test4"))
    handler.add_model(model)
    handler.remove_model(model="test2")
    assert len(handler.get_models()) == 1
    assert model_collection.count_documents({}) == 1
    assert model_collection.count_documents({"model.id": "test2"}) == 0
    assert model_collection.count_documents({"model.id": "test"}) == 1

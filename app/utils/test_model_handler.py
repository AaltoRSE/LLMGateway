from pytest_mock_resources import create_redis_fixture
from pytest_mock_resources import create_mongo_fixture
from model_handler import ModelHandler
from api_requests import AddAvailableModelRequest, RemoveModelRequest

redis = create_redis_fixture()
mongo = create_mongo_fixture()


# Testing whether keys are checked correctly
def test_add_model(redis, mongo):
    handler = ModelHandler(True)
    handler.setup(mongo, redis)
    currentModels = handler.get_models()
    db = mongo["gateway"]
    model_collection = db["model"]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    addRequest = AddAvailableModelRequest(
        model="test", target_path="test2", owner="test3"
    )
    handler.add_model(addRequest)
    # Adding model works
    assert model_collection.count_documents({}) == 1
    failed = False
    try:
        addRequest = AddAvailableModelRequest(
            model="test", target_path="test2", owner="test3"
        )
        handler.add_model(addRequest)
    except KeyError as e:
        failed = True
    assert failed
    addRequest = AddAvailableModelRequest(
        model="test2", target_path="test2", owner="test3"
    )
    handler.add_model(addRequest)
    # Adding second model works
    assert model_collection.count_documents({}) == 2


def test_model_path_and_get(redis, mongo):
    handler = ModelHandler(True)
    handler.setup(mongo, redis)
    currentModels = handler.get_models()
    db = mongo["gateway"]
    model_collection = db["model"]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    addRequest = AddAvailableModelRequest(
        model="test", target_path="test2", owner="test3"
    )
    handler.add_model(addRequest)
    assert model_collection.count_documents({}) == 1
    addRequest = AddAvailableModelRequest(
        model="test2", target_path="test2", owner="test4"
    )
    handler.add_model(addRequest)
    models = handler.get_models()
    assert len(models) == 2
    found1 = False
    found2 = False
    for model in models:
        if model["id"] == "test":
            found1 = True
            assert model["owned_by"] == "test3"
            assert len(model["permissions"]) == 0
            assert model["object"] == "model"
        if model["id"] == "test2":
            found2 = True
            assert model["owned_by"] == "test4"
            assert len(model["permissions"]) == 0
            assert model["object"] == "model"

    assert found1 and found2

    addRequest = AddAvailableModelRequest(
        model="test3", target_path="test3", owner="test3"
    )
    handler.add_model(addRequest)
    assert model_collection.count_documents({}) == 3
    assert handler.get_model_path("test") == "test2"
    assert handler.get_model_path("test2") == "test2"
    assert handler.get_model_path("test3") == "test3"
    models = handler.get_models()
    assert len(models) == 3


def test_remove_model(redis, mongo):
    handler = ModelHandler(True)
    handler.setup(mongo, redis)
    currentModels = handler.get_models()
    db = mongo["gateway"]
    model_collection = db["model"]
    assert len(currentModels) == 0
    assert model_collection.count_documents({}) == 0
    addRequest = AddAvailableModelRequest(
        model="test", target_path="test2", owner="test3"
    )
    handler.add_model(addRequest)
    addRequest = AddAvailableModelRequest(
        model="test2", target_path="test2", owner="test4"
    )
    handler.add_model(addRequest)
    removeRequest = RemoveModelRequest(model="test2")
    handler.remove_model(removeRequest)
    assert len(handler.get_models()) == 1
    assert model_collection.count_documents({}) == 1
    assert model_collection.count_documents({"data.id": "test2"}) == 0
    assert model_collection.count_documents({"data.id": "test"}) == 1

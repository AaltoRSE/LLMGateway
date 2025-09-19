import pytest
from fastapi import HTTPException
from tests.fixtures.db_fixtures import Repositories
from app.services.model_service import ModelService
from app.schemas.llmmodel_schema import LLMModelData, LLMModelDataDetails


def create_test_model(path="test", host="http://host.svc", id="test", owned_by="test3"):
    return LLMModelData(
        path=path,
        host=host,
        name="Test Model",
        description="A Model for testing purposes",
        model=LLMModelDataDetails(id=id, owned_by=owned_by),
    )


@pytest.mark.asyncio
async def test_init_models(
    model_service: ModelService, mock_repositories: Repositories
):
    testmodel = create_test_model()
    await mock_repositories.model_repo.add_model(testmodel)
    with pytest.raises(HTTPException) as execinfo:
        model_service.get_model(testmodel.model.id)
    assert execinfo.value.status_code == 404
    models = await model_service.get_api_models()
    assert len(models) == 1
    # now init.
    await model_service.init_models()
    model = await model_service.get_model(testmodel.model.id)
    assert model.model.path == testmodel.path


# Testing whether keys are checked correctly
@pytest.mark.asyncio
async def test_add_model(model_service: ModelService, mock_repositories: Repositories):
    await model_service.init_models()
    currentModels = model_service.get_api_models()
    assert len(currentModels) == 0
    assert len(mock_repositories.model_repo.__class__.models.values()) == 0
    model = create_test_model(path="test", id="test")
    await model_service.add_model(model)
    # Adding model works
    assert len(mock_repositories.model_repo.__class__.models.values()) == 1
    with pytest.raises(HTTPException) as execinfo:
        model = create_test_model(path="test2", id="test")
        await model_service.add_model(model)
    assert execinfo.value.status_code == 409

    model = create_test_model(path="test2", id="test2")
    model_service.add_model(model)
    # Adding second model works
    assert len(mock_repositories.model_repo.__class__.models.values()) == 2


# Testing whether keys are checked correctly
@pytest.mark.asyncio
async def test_update_model(
    model_service: ModelService, mock_repositories: Repositories
):
    await model_service.init_models()
    currentModels = model_service.get_api_models()
    assert len(currentModels) == 0
    model = create_test_model(path="test", id="test")
    await model_service.add_model(model)
    created_model = await model_service.get_model(model.model.id)
    model.model.owned_by = "Someone"
    model.path = "this/is/the/new/path"
    await model_service.update_model(model)
    changed_model = await model_service.get_model(model.model.id)
    assert created_model.model.model.owned_by != changed_model.model.model.owned_by
    assert created_model.model.path != changed_model.model.path
    assert changed_model.model.model.owned_by == "Someone"
    assert changed_model.model.path == "this/is/the/new/path"


@pytest.mark.asyncio
async def test_get_model_path(
    model_service: ModelService, mock_repositories: Repositories
):
    model = create_test_model(path="test2")
    await model_service.add_model(model)
    model = create_test_model(path="test2", id="test2", owned_by="test4")
    await model_service.add_model(model)
    models = await model_service.get_api_models()
    assert len(models) == 2
    found1 = False
    found2 = False
    for model in models:
        if model.model.id == "test":
            found1 = True
            assert model.model.owned_by == "test3"
            assert len(model.model.permissions) == 0
            assert model.model.object == "model"
        if model.model.id == "test2":
            found2 = True
            assert model.model.owned_by == "test4"
            assert len(model.model.permissions) == 0
            assert model.model.object == "model"

    assert found1 and found2
    model = create_test_model(path="test3", id="test3")
    await model_service.add_model(model)
    assert len(mock_repositories.model_repo.__class__.models.values()) == 3
    host, path = await model_service.get_model_location("test")
    host2, path2 = await model_service.get_model_location("test2")
    host3, path3 = await model_service.get_model_location("test")
    assert path == "test2"
    assert path2 == "test2"
    assert path3 == "test3"
    models = model_service.get_api_models()
    assert len(models) == 3


@pytest.mark.asyncio
async def test_get_model(model_service: ModelService, mock_repositories: Repositories):
    await model_service.init_models()
    currentModels = model_service.get_api_models()
    assert len(currentModels) == 0
    model1 = create_test_model(path="test2")
    await model_service.add_model(model1)
    model2 = create_test_model(path="test2", id="test2", owned_by="test4")
    await model_service.add_model(model2)
    model1_retrieved = await model_service.get_model(model1.model.id)
    assert model1_retrieved.model.model.owned_by == "test3"
    assert model1_retrieved.model.path == model1.path

    model2_retrieved = await model_service.get_model(model2.model.id)
    assert model2_retrieved.model.model.owned_by == "test4"
    assert model2_retrieved.model.path == model2.path


@pytest.mark.asyncio
async def test_remove_model(
    model_service: ModelService, mock_repositories: Repositories
):
    await model_service.init_models()
    currentModels = await model_service.get_api_models()
    assert len(currentModels) == 0
    model = create_test_model(path="test2")
    await model_service.add_model(model)
    model = create_test_model(path="test2", id="test2", owned_by="test4")
    await model_service.add_model(model)
    await model_service.remove_model(model="test2")
    assert len(await model_service.get_api_models()) == 1
    assert len(mock_repositories.model_repo.__class__.models.values()) == 1
    with pytest.raises(HTTPException) as execinfo:
        await model_service.remove_model(model="test3")
    assert execinfo.value.status_code == 410
    assert len(mock_repositories.model_repo.__class__.models.values()) == 1
    remaining_models = await mock_repositories.model_repo.get_models()
    assert len(remaining_models) == 1
    assert remaining_models[0].model.id == "test"

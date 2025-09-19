from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.schemas.llmmodel_schema import LLMModelData, LLMModelDataDetails
from app.requests.admin_requests import *
from app.services.user_service import UserService
from app.services.key_service import KeyService
from app.services.model_service import ModelService
from app.services.usage_service import UsageService
from app.services.model_service import ModelService
from tests.fixtures.db_fixtures import Repositories
import pytest


@pytest.mark.asyncio
async def test_add_remove_update_and_get_model_admin(
    mock_repositories: Repositories,
    redis_dbs,
    admin_key_client: TestClient,
    model_service: ModelService,
):
    request = LLMModelData(
        path="testpath",
        name="test",
        description="test",
        host="http://host.svc",
        model=LLMModelDataDetails(
            id="test",
            owned_by="Test",
        ),
    )
    response = admin_key_client.post("/admin/addmodel", json=request.model_dump())
    assert response.status_code == 201
    models = await model_service.get_models()
    assert len(models) == 1
    assert models[0].name == "test"
    request2 = request.model_copy(deep=True)
    request2.path = "testpath2"
    request2.model.id = "test2"
    response2 = admin_key_client.post("/admin/addmodel", json=request2.model_dump())
    assert response2.status_code == 201
    models = await model_service.get_models()
    assert len(models) == 2
    model_path_1, model_host_1 = await model_service.get_model_location("test", "chat")
    model_path_2, model_host_2 = await model_service.get_model_location("test2", "chat")
    assert model_path_1 == "testpath"
    assert model_host_1 == "http://host.svc"
    assert model_path_2 == "testpath2"
    assert model_host_2 == "http://host.svc"
    # No conflict allowed
    response3 = admin_key_client.post("/admin/addmodel", json=request.model_dump())
    assert response3.status_code == 409
    # Lets get the models
    response3 = admin_key_client.get("/admin/models")
    assert response3.status_code == 200
    models = response3.json()
    assert len(models) == 2
    assert set([model["model"]["id"] for model in models]) == set(["test", "test2"])

    # Remove the model
    request3 = RemoveModelRequest(model="test")
    response4 = admin_key_client.post("/admin/removemodel", json=request3.model_dump())
    assert response4.status_code == 200
    assert len(await model_service.get_models()) == 1
    with pytest.raises(HTTPException) as execinfo:
        await model_service.get_model_location("test", "chat")
    assert execinfo.value.status_code == 404

    # Can't remove it again.
    response4 = admin_key_client.post("/admin/removemodel", json=request3.model_dump())
    assert response4.status_code == 410
    response3 = admin_key_client.get("/admin/models")
    assert response3.status_code == 200
    models = response3.json()
    assert len(models) == 1
    assert set([model["model"]["id"] for model in models]) == set(["test2"])
    request2.path = "/new/path"
    response = admin_key_client.post("/admin/update_model", json=request2.model_dump())
    assert response.status_code == 200
    model_path_2, model_host_2 = await model_service.get_model_location("test2")
    assert model_path_2 == "/new/path"


@pytest.mark.asyncio
async def test_reset_user(
    admin_client: TestClient, mock_repositories: Repositories, redis_dbs
):
    user_service = UserService(
        user_respository=mock_repositories.user_repo,
        key_repository=mock_repositories.key_repo,
    )
    await user_service.get_or_create_user_from_auth_data(
        "test", "test", "test", ["employee"]
    )
    await user_service.update_agreement_version("test", "1.0")
    # Also manual set a key, which will be removed by the reset
    request = UserRequest(username="test")
    user = await user_service.get_user_by_id("test")
    assert user.accepted_agreement_version == "1.0"
    response = admin_client.post("/admin/reset_user", json=request.model_dump())
    assert response.status_code == 200
    user = await user_service.get_user_by_id("test")
    assert user.accepted_agreement_version == ""
    request = UserRequest(username="test2")
    response = admin_client.post("/admin/reset_user", json=request.model_dump())
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_keys(admin_client: TestClient):
    user_service = UserService()
    user_service.get_or_create_user_from_auth_data(
        "test", "test", "test", "thi@test.fi", ["employee"]
    )
    key_service = KeyService()
    key1 = key_service.create_key("test", "test")
    key2 = key_service.create_key("Admin", "admin")
    key3 = key_service.create_key("Admin", "admin")
    response = admin_client.get("/admin/listkeys")
    assert response.status_code == 200
    listed_keys = response.json()
    created_keys = [key1.key, key2.key, key3.key]
    for key in listed_keys:
        assert key["key"] in created_keys
        assert key["active"] == True

    key4 = key_service.create_key("Admin", "admin")
    response = admin_client.get("/admin/listkeys")
    assert key4.key in [key["key"] for key in response.json()]


@pytest.mark.asyncio
async def test_list_users(admin_client: TestClient):
    user_service = UserService()
    user_service.get_or_create_user_from_auth_data(
        "test", "test", "test", "thi@test.fi", ["employee"]
    )
    key_service = KeyService()
    key1 = key_service.create_key("test", "test")
    response = admin_client.post("/admin/list_users")
    assert response.status_code == 200
    print(response)
    print(response.content)
    listed_users = response.json()
    assert len(listed_users) == 2  # Admin and test user
    assert "Admin" in [user["auth_id"] for user in listed_users]
    assert "test" in [user["auth_id"] for user in listed_users]
    user_service.get_or_create_user_from_auth_data(
        "test2", "test2", "test2", "thi@test2.fi", ["employee"]
    )
    response = admin_client.post("/admin/list_users")
    assert response.status_code == 200
    listed_users = response.json()
    assert len(listed_users) == 3  # Admin and test user


@pytest.mark.asyncio
async def test_set_admin(admin_client: TestClient):
    user_service = UserService()
    user_service.get_or_create_user_from_auth_data(
        "test", "test", "test", "thi@test.fi", ["employee"]
    )
    response = admin_client.post(
        "/admin/set_admin", json={"username": "test", "admin": True}
    )
    assert response.status_code == 200
    response = admin_client.post("/admin/list_users")
    for admin_status in [user["admin"] for user in response.json()]:
        # Everyone is admin
        assert admin_status
    response = admin_client.post(
        "/admin/set_admin", json={"username": "test", "admin": False}
    )
    assert response.status_code == 200
    response = admin_client.post("/admin/list_users")
    user = [user for user in response.json() if user["auth_id"] == "test"][0]
    assert not user["admin"]
    response = admin_client.post(
        "/admin/set_admin", json={"username": "Admin", "admin": True}
    )
    # Changing own admin status not allowed
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_usage_for_user(admin_client: TestClient):
    usage_service = UsageService()
    user_service = UserService()
    key_service = KeyService()
    user_service.get_or_create_user_from_auth_data(
        "test", "test", "test", "thi@test.fi", ["employee"]
    )
    key = key_service.create_key("test", "test")
    key2 = key_service.create_key("Admin", "admin")
    requestUsage = RequestUsage(
        prompt_tokens=10, completion_tokens=10, prompt_cost=0.1, completion_cost=0.1
    )
    usage_service.add_persistent_usage("model1", key, requestUsage)
    usage_service.add_persistent_usage("model1", key, requestUsage)
    usage_service.add_persistent_usage("model2", key, requestUsage)
    usage_service.add_persistent_usage("model2", key, requestUsage)
    usage_service.add_persistent_usage("model1", key2, requestUsage)
    usage_service.add_persistent_usage("model2", key2, requestUsage)
    user_response = admin_client.post(
        "/admin/get_usage_for_user", json={"username": "test"}
    )
    admin_response = admin_client.post(
        "/admin/get_usage_for_user", json={"username": "Admin"}
    )
    assert user_response.status_code == 200
    assert admin_response.status_code == 200
    user_usage = user_response.json()
    print(user_usage)
    admin_usage = admin_response.json()
    print(admin_usage)
    # This is either one or 2 hours... depending on when the test is run...
    assert len(user_usage) == 2 or len(user_usage) == 1
    if len(user_usage) == 2:
        firstHour = PerHourUsage.model_validate(user_usage[0])
        secondHour = PerHourUsage.model_validate(user_usage[1])
        user_usage = PerHourUsage(
            timestamp=firstHour.timestamp,
            cost=firstHour.cost + secondHour.cost,
            prompt_tokens=firstHour.prompt_tokens + secondHour.prompt_tokens,
            completion_tokens=firstHour.completion_tokens
            + secondHour.completion_tokens,
        )
    else:
        user_usage = PerHourUsage.model_validate(user_usage[0])
    assert user_usage.cost == 8
    assert user_usage.prompt_tokens == 40
    assert user_usage.completion_tokens == 40
    assert len(admin_usage) == 2 or len(admin_usage) == 1
    if len(admin_usage) == 2:
        firstHour = PerHourUsage.model_validate(admin_usage[0])
        secondHour = PerHourUsage.model_validate(admin_usage[1])
        admin_usage = PerHourUsage(
            timestamp=firstHour.timestamp,
            cost=firstHour.cost + secondHour.cost,
            prompt_tokens=firstHour.prompt_tokens + secondHour.prompt_tokens,
            completion_tokens=firstHour.completion_tokens
            + secondHour.completion_tokens,
        )
    else:
        admin_usage = PerHourUsage.model_validate(admin_usage[0])
    assert admin_usage.cost == 4


@pytest.mark.asyncio
async def test_no_access_user(user_client: TestClient):
    request = admin.AddAvailableModelRequest(
        id="test", path="test", name="test", description="test"
    )
    response = user_client.post("/admin/addmodel", json=request.model_dump())
    assert response.status_code == 403
    response = user_client.post("/admin/removemodel", json=request.model_dump())
    assert response.status_code == 403
    response = user_client.post("/admin/reset_user", json=request.model_dump())
    assert response.status_code == 403
    response = user_client.post("/admin/listkeys", json=request.model_dump())
    assert response.status_code == 403
    response = user_client.post("/admin/list_users", json=request.model_dump())
    assert response.status_code == 403
    response = user_client.post("/admin/set_admin", json=request.model_dump())
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_no_access_no_user(unauthed_client: TestClient):
    request = admin.AddAvailableModelRequest(
        id="test", path="test", name="test", description="test"
    )
    response = unauthed_client.post("/admin/addmodel", json=request.model_dump())
    assert response.status_code == 401
    response = unauthed_client.post("/admin/removemodel", json=request.model_dump())
    assert response.status_code == 401
    response = unauthed_client.post("/admin/reset_user", json=request.model_dump())
    assert response.status_code == 401
    response = unauthed_client.post("/admin/listkeys", json=request.model_dump())
    assert response.status_code == 401
    response = unauthed_client.post("/admin/list_users", json=request.model_dump())
    assert response.status_code == 401
    response = unauthed_client.post("/admin/set_admin", json=request.model_dump())
    assert response.status_code == 401

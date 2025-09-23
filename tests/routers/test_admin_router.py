from datetime import datetime
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.schemas.llmmodel_schema import LLMModelData, LLMModelDataDetails
from app.schemas.user_schema import SessionAuthData
from app.requests.admin_requests import *
from app.services.user_service import UserService, User
from app.services.key_service import KeyService, APIKey
from app.services.model_service import ModelService
from app.services.usage_service import UsageService, RequestSource, APIRequest, Balance
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
    model_path_2, model_host_2 = await model_service.get_model_location("test2", "chat")
    assert model_path_2 == "/new/path"


@pytest.mark.asyncio
async def test_reset_user(
    admin_session_client: TestClient,
    admin_key_client: TestClient,
    mock_repositories: Repositories,
    redis_dbs,
    user_service: UserService,
):
    user = await user_service.get_or_create_user_from_auth_data(
        SessionAuthData(
            auth_id="test", first_name="test", last_name="test", roles=["employee"]
        )
    )
    await user_service.update_agreement_version(user.id, "1.0")
    # Also manual set a key, which will be removed by the reset
    request = UserRequest(user_id=user.id)
    user = await user_service.get_user_by_auth_id("test")
    assert user.accepted_agreement_version == "1.0"
    response = admin_session_client.post("/admin/reset_user", json=request.model_dump())
    print(response.json())
    assert response.status_code == 200
    user = await user_service.get_user_by_auth_id("test")
    assert user.accepted_agreement_version == "0.0"
    request = UserRequest(user_id="test2")
    response = admin_key_client.post("/admin/reset_user", json=request.model_dump())
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_keys(
    admin_session_client: TestClient,
    key_service: KeyService,
    admin_user: User,
    normal_user,
):

    key1 = await key_service.create_key("test", normal_user.id)
    key2 = await key_service.create_key("Admin", admin_user.id)
    key3 = await key_service.create_key("Admin", admin_user.id)
    response = admin_session_client.get("/admin/listkeys")
    assert response.status_code == 200
    listed_keys = response.json()
    created_keys = [key1.key, key2.key, key3.key]
    for key in listed_keys:
        assert key["key"] in created_keys
        assert key["active"] == True

    key4 = await key_service.create_key("Admin", admin_user.id)
    response = admin_session_client.get("/admin/listkeys")
    assert key4.key in [key["key"] for key in response.json()]


@pytest.mark.asyncio
async def test_list_users(
    admin_session_client: TestClient,
    normal_user: User,
    admin_user: User,
    user_service: UserService,
):

    response = admin_session_client.post("/admin/list_users")
    assert response.status_code == 200
    print(response)
    print(response.content)
    listed_users = response.json()
    assert len(listed_users) == 2  # Admin and test user
    assert admin_user.auth_id in [user["auth_id"] for user in listed_users]
    assert normal_user.auth_id in [user["auth_id"] for user in listed_users]
    await user_service.get_or_create_user_from_auth_data(
        SessionAuthData(
            auth_id="test2", first_name="test2", last_name="test2", roles=["employee"]
        )
    )
    response = admin_session_client.post("/admin/list_users")
    assert response.status_code == 200
    listed_users = response.json()
    assert len(listed_users) == 3  # Admin and test user


@pytest.mark.asyncio
async def test_set_admin(
    admin_session_client: TestClient, admin_user: User, normal_user: User
):
    response = admin_session_client.post(
        "/admin/set_admin", json={"user_id": normal_user.id, "admin": True}
    )
    assert response.status_code == 200
    response = admin_session_client.post("/admin/list_users")
    for admin_status in [user["admin"] for user in response.json()]:
        # Everyone is admin
        assert admin_status
    response = admin_session_client.post(
        "/admin/set_admin", json={"user_id": normal_user.id, "admin": False}
    )
    assert response.status_code == 200
    response = admin_session_client.post("/admin/list_users")
    user = [user for user in response.json() if user["auth_id"] == normal_user.auth_id][
        0
    ]
    assert not user["admin"]
    response = admin_session_client.post(
        "/admin/set_admin", json={"user_id": admin_user.id, "admin": True}
    )
    # Changing own admin status not allowed
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_usage_for_user_and_balance_per_user(
    admin_session_client: TestClient,
    normal_user: User,
    usage_service: UsageService,
    key_service: KeyService,
    admin_user: User,
):
    user_key: APIKey = await key_service.create_key(
        name="UserKey", user_id=normal_user.id
    )
    admin_key = await key_service.create_key(name="AdminKey", user_id=admin_user.id)
    user_source = RequestSource(user_id=normal_user.id, key=user_key.key)
    request = APIRequest(
        completion_tokens=10,
        prompt_tokens=10,
        cost=1.0,
        model="Test",
        timestamp=datetime.now(),
    )
    admin_source = RequestSource(user_id=admin_user.id, key=admin_key.key)

    await usage_service.log_usage(source=user_source, usage=request)
    await usage_service.log_usage(source=user_source, usage=request)
    await usage_service.log_usage(source=admin_source, usage=request)
    request.model = "SecondModel"
    await usage_service.log_usage(source=admin_source, usage=request)
    await usage_service.log_usage(source=user_source, usage=request)
    user_response = admin_session_client.post(
        "/admin/get_usage_for_user", json={"user_id": normal_user.id}
    )
    admin_response = admin_session_client.post(
        "/admin/get_usage_for_user", json={"user_id": admin_user.id}
    )
    assert user_response.status_code == 200
    assert admin_response.status_code == 200
    user_usage = user_response.json()
    print(user_usage)
    admin_usage = admin_response.json()
    print(admin_usage)
    # This is either one or 2 hours... depending on when the test is run...
    assert len(user_usage) == 3
    assert len(admin_usage) == 2
    balance_response = admin_session_client.get("/admin/get_balance_per_user")
    print(balance_response.json())
    balances = [Balance.model_validate(balance) for balance in balance_response.json()]
    assert len(balances) == 2
    if balances[0].user_id == admin_user.id:
        admin_balance = balances[0]
        user_balance = balances[1]
    else:
        admin_balance = balances[1]
        user_balance = balances[0]
    assert admin_balance.balance_used == 2.0
    assert user_balance.balance_used == 3.0


@pytest.mark.asyncio
async def test_no_access_user(normal_session_client: TestClient):
    request = UserRequest(user_id="blubb")
    response = normal_session_client.post("/admin/addmodel", json=request.model_dump())
    assert response.status_code == 403
    response = normal_session_client.post(
        "/admin/removemodel", json=request.model_dump()
    )
    assert response.status_code == 403
    response = normal_session_client.post(
        "/admin/reset_user", json=request.model_dump()
    )
    assert response.status_code == 403
    response = normal_session_client.post("/admin/listkeys", json=request.model_dump())
    assert response.status_code == 403
    response = normal_session_client.post(
        "/admin/list_users", json=request.model_dump()
    )
    assert response.status_code == 403
    response = normal_session_client.post("/admin/set_admin", json=request.model_dump())
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_no_access_no_user(unauthed_client: TestClient):
    request = UserRequest(user_id="blubb")

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

from fastapi import HTTPException
from app.routers.tests.mocks import mockAdminUserAuth, mockNormalUserAuth
import app.middleware.authentication_middleware as auth_middleware
from fastapi.testclient import TestClient
import pytest
import app.requests.admin_requests as admin
from app.services.model_service import ModelService
from app.services.user_service import UserService
from app.services.key_service import KeyService
import app.db.mongo as mongo


@pytest.fixture()
def admin_client(monkeypatch) -> TestClient:
    authmock = mockAdminUserAuth()
    monkeypatch.setattr(
        auth_middleware.SessionAuthenticationBackend,
        "authenticate",
        authmock,
    )
    import app.main

    return TestClient(app.main.app)


@pytest.fixture()
def user_client(monkeypatch) -> TestClient:
    authmock = mockNormalUserAuth()
    monkeypatch.setattr(
        auth_middleware.SessionAuthenticationBackend,
        "authenticate",
        authmock,
    )
    import app.main

    return TestClient(app.main.app)


@pytest.fixture()
def unauthed_client() -> TestClient:
    import app.main

    return TestClient(app.main.app)


def test_add_remove_update_and_get_model_admin(admin_client: TestClient):
    request = admin.AddAvailableModelRequest(
        id="test", path="test", name="test", description="test"
    )
    response = admin_client.post("/admin/addmodel", json=request.model_dump())
    assert response.status_code == 201
    service = ModelService()
    models = service.get_models()
    assert len(models) == 1
    assert models[0].name == "test"
    request2 = admin.AddAvailableModelRequest(
        id="test2", path="test2", name="test2", description="test2"
    )
    response2 = admin_client.post("/admin/addmodel", json=request2.model_dump())
    assert response2.status_code == 201
    models = service.get_models()
    assert len(models) == 2
    assert service.get_model_path("test2") == "test2"
    assert service.get_model_path("test") == "test"
    # No conflict allowed
    response3 = admin_client.post("/admin/addmodel", json=request.model_dump())
    assert response3.status_code == 409
    # Lets get the models
    response3 = admin_client.get("/admin/models")
    assert response3.status_code == 200
    models = response3.json()
    assert len(models) == 2
    assert set([model["model"]["id"] for model in models]) == set(["test", "test2"])

    # Remove the model
    request3 = admin.RemoveModelRequest(model="test")
    response4 = admin_client.post("/admin/removemodel", json=request3.model_dump())
    assert response4.status_code == 200
    assert len(service.get_models()) == 1
    try:
        service.get_model_path("test")
        assert False
    except HTTPException as e:
        assert e.status_code == 404
        assert e.detail == f"Model test not found"
    # Can't remove it again.
    response4 = admin_client.post("/admin/removemodel", json=request3.model_dump())
    assert response4.status_code == 410
    response3 = admin_client.get("/admin/models")
    assert response3.status_code == 200
    models = response3.json()
    assert len(models) == 1
    assert set([model["model"]["id"] for model in models]) == set(["test2"])
    request2.path = "/new/path"
    response = admin_client.post("/admin/update_model", json=request2.model_dump())
    assert response.status_code == 200
    assert service.get_model_path("test2") == "/new/path"


def test_reset_user(admin_client: TestClient):
    user_service = UserService()
    user_service.get_or_create_user_from_auth_data(
        "test", "test", "test", "thi@test.fi"
    )
    user_service.update_agreement_version("test", "1.0")
    # Also manual set a key, which will be removed by the reset
    user_service.user_collection.update_one(
        {mongo.ID_FIELD: "test"}, {"$set": {"keys": ["test"]}}
    )
    request = admin.UserRequest(username="test")
    user = user_service.get_user_by_id("test")
    assert user.seen_guide_version == "1.0"
    response = admin_client.post("/admin/reset_user", json=request.model_dump())
    assert response.status_code == 200
    user = user_service.get_user_by_id("test")
    assert user.seen_guide_version == ""
    assert user.keys == []
    request = admin.UserRequest(username="test2")
    response = admin_client.post("/admin/reset_user", json=request.model_dump())
    assert response.status_code == 404


def test_list_keys(admin_client: TestClient):
    user_service = UserService()
    user_service.get_or_create_user_from_auth_data(
        "test", "test", "test", "thi@test.fi"
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


def test_list_users(admin_client: TestClient):
    user_service = UserService()
    user_service.get_or_create_user_from_auth_data(
        "test", "test", "test", "thi@test.fi"
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
        "test2", "test2", "test2", "thi@test2.fi"
    )
    response = admin_client.post("/admin/list_users")
    assert response.status_code == 200
    listed_users = response.json()
    assert len(listed_users) == 3  # Admin and test user


def test_set_admin(admin_client: TestClient):
    user_service = UserService()
    user_service.get_or_create_user_from_auth_data(
        "test", "test", "test", "thi@test.fi"
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


def test_no_access_user(user_client: TestClient):
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


def test_no_access_no_user(unauthed_client: TestClient):
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

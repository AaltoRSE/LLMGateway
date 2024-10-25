from app.routers.tests.mocks import mockAdminUserAuth, mockNormalUserAuth

import app.middleware.authentication_middleware as auth_middleware
from fastapi.testclient import TestClient
import pytest
import app.db.mongo


@pytest.fixture()
def admin_client(monkeypatch):
    authmock = mockAdminUserAuth()
    monkeypatch.setattr(
        auth_middleware.SessionAuthenticationBackend,
        "authenticate",
        authmock,
    )
    import app.main

    return TestClient(app.main.app)


@pytest.fixture()
def user_client(monkeypatch):
    authmock = mockNormalUserAuth()
    monkeypatch.setattr(
        auth_middleware.SessionAuthenticationBackend,
        "authenticate",
        authmock,
    )
    import app.main

    return TestClient(app.main.app)


@pytest.fixture()
def unauthed_client():
    import app.main

    return TestClient(app.main.app)


def test_admin_user(admin_client):
    response = admin_client.get("/auth/test")
    assert response.status_code == 200
    assert response.json() == {
        "authed": True,
        "user": "Admin",
        "agreement_ok": True,
        "admin": True,
    }


def test_normal_user(user_client):
    response = user_client.get("/auth/test")
    assert response.status_code == 200
    assert response.json() == {
        "authed": True,
        "user": "User",
        "agreement_ok": True,
        "admin": False,
    }


def test_no_user(unauthed_client):
    response = unauthed_client.get("/auth/test")
    assert response.status_code == 200
    assert response.json() == {"authed": False, "reason": "No user authenticated"}

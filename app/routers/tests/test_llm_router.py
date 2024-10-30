from fastapi import HTTPException
from app.routers.tests.mocks import mockAdminUserAuth, mockNormalUserAuth
import app.middleware.authentication_middleware as auth_middleware
from fastapi.testclient import TestClient
import pytest
import respx
import app.requests.admin_requests as admin
from app.models.model import LLMModel, LLMModelData
from app.services.model_service import ModelService
from app.services.user_service import UserService
from app.services.key_service import KeyService
from app.services.usage_service import UsageService
import app.db.mongo as mongo
from app.models.quota import (
    UsageElements,
    UsagePerKeyForUser,
    KeyPerModelUsage,
    ModelUsage,
    PerHourUsage,
    PerUserUsage,
    PerModelUsage,
    UsageElements,
    DEFAULT_USAGE,
    RequestUsage,
)
import httpx

default_response = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-4o-mini",
    "system_fingerprint": "fp_44709d6fcb",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "\n\nHello there, how may I assist you today?",
            },
            "logprobs": None,
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 9,
        "completion_tokens": 12,
        "total_tokens": 21,
        "completion_tokens_details": {"reasoning_tokens": 0},
    },
}


model_path = "http://llm.model"

chat_path = "/v1/chat/completions"
completion_path = "/v1/completions"
embedding_path = "/v1/embeddings"


@pytest.fixture()
def unauthed_client() -> TestClient:
    import app.main

    return TestClient(app.main.app)


@pytest.fixture()
def api_key(monkeypatch):
    monkeypatch.setenv("INFERENCE_KEY", "Test_key")
    yield  # This is the magical bit which restore the environment after


def test_chat_completion(
    unauthed_client: TestClient, respx_mock: respx.MockRouter, api_key
):
    llm_chat = respx_mock.post(f"{model_path}{chat_path}").mock(
        return_value=httpx.Response(200, json=default_response)
    )
    key_service = KeyService()
    key = key_service.create_key(user="Admin", name="test", user_key=False)
    model_service = ModelService()
    model_service.add_model(
        LLMModel(
            path=model_path,
            name="Test",
            description="Test",
            model=LLMModelData(id="gpt-4o-mini", owned_by="test"),
        )
    )
    unauthed_client.headers["Authorization"] = f"Bearer {key.key}"
    response = unauthed_client.post(
        chat_path,
        json={
            "prompt": "Hello there, how may I assist you today?",
            "model": "gpt-4o-mini",
        },
    )
    data = response.json()
    print(data)
    assert (
        data["choices"][0]["message"]["content"]
        == "\n\nHello there, how may I assist you today?"
    )
    assert len(data["choices"]) == 1
    quota_service = UsageService()
    quota_service.get_usage_for_key(key.key)
    assert quota_service.get_usage_for_key(key.key).prompt_tokens == 9
    assert llm_chat.called
    assert llm_chat.calls[0].request.headers["Authorization"] == f"Bearer Test_key"

import re
from typing import Any, AsyncIterator, List
import pytest
from fastapi.testclient import TestClient
import respx
import asyncio
from app.services.usage_service import UsageService
from app.services.model_service import ModelService
from app.services.balance_service import BalanceService
from tests.fixtures.db_fixtures import Repositories
from app.security.auth import BackendUser
from app.schemas.user_schema import User
from app.utils.llm_model import LLMModel
from app.schemas.openai_schemas import (
    PromptTokensDetails,
    ResponseUsage,
    InputTokensDetails1,
    OutputTokensDetails,
    CreateResponse,
    CompletionUsage,
)


async def collect_async_iterator(async_iter: AsyncIterator[Any]) -> List[Any]:
    return [item async for item in async_iter]


@pytest.mark.asyncio
async def test_completions_endpoint(
    key_client: TestClient,
    general_api: LLMModel,
    usage_service: UsageService,
    balance_service: BalanceService,
    normal_user: User,
    mock_repositories: Repositories,
) -> None:
    request: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": "whatever"},
            {"role": "user", "content": "whatever more"},
        ],
        "model": general_api.model.model.id,
    }

    # Make sure no usage happened yet
    balance = await usage_service.get_current_user_balance(normal_user.id)
    assert balance.balance_used == 0
    response = key_client.post("/api/v1/chat/completions", json=request)
    assert response.status_code == 200
    result = response.json()
    assert "choices" in result
    assert "usage" in result
    assert result["usage"]["prompt_tokens"] == 1117
    usage = CompletionUsage.model_validate(result["usage"])
    balance = await usage_service.get_current_user_balance(normal_user.id)
    cost = general_api.calc_cost_from_chat_usage(usage)
    assert balance.balance_used == pytest.approx(cost)
    assert balance.balance_used > 0
    # use a streamig response
    request["stream"] = True
    response = key_client.post("/api/v1/chat/completions", json=request)
    assert response.status_code == 200
    # Process the response
    async for item in response.aiter_text():
        print(item)
        pass
    service_balance = await balance_service.get_user_balance(normal_user.id)
    assert service_balance.balance_used > 0
    print("Finished")
    new_balance = await usage_service.get_current_user_balance(normal_user.id)
    assert new_balance.balance_used > balance.balance_used
    # TODO: test invalid models


@pytest.mark.asyncio
async def test_responses_dont_work_for_completions(
    key_client: TestClient,
    completions_api: LLMModel,
) -> None:
    request: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": "whatever"},
            {"role": "user", "content": "whatever more"},
        ],
        "model": completions_api.model.model.id,
    }
    # Make sure no usage happened yet
    response = key_client.post("/api/v1/chat/completions", json=request)
    assert response.status_code == 200
    request: dict[str, Any] = {
        "input": [
            {"role": "system", "content": "whatever"},
            {"role": "user", "content": "whatever more"},
        ],
        "model": completions_api.model.model.id,
    }
    response = key_client.post("/api/v1/responses", json=request)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_embeddings_endpoint(
    key_client: TestClient,
    normal_user: BackendUser,
    general_api: LLMModel,
    mock_repositories: Repositories,
    usage_service: UsageService,
) -> None:
    request = {"input": "Irrelevant", "model": general_api.model.model.id}
    # Make sure no usage happened yet
    balance = await usage_service.get_current_user_balance(normal_user.id)
    assert balance.balance_used == 0
    response = key_client.post("/api/v1/embeddings", json=request)

    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert "usage" in result
    assert result["usage"]["prompt_tokens"] == 1
    assert len(result["data"][0]["embedding"]) == 512
    balance = await usage_service.get_current_user_balance(normal_user.id)
    assert balance.balance_used > 0
    request: dict[str, Any] = {
        "input": "Irrelevant",
        "model": general_api.model.model.id,
        "dimensions": 20,
    }
    response = key_client.post("/api/v1/embeddings", json=request)
    new_balance = await usage_service.get_current_user_balance(normal_user.id)
    assert new_balance.balance_used > balance.balance_used
    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert "usage" in result
    assert result["usage"]["prompt_tokens"] == 1
    assert len(result["data"][0]["embedding"]) == 20
    # TODO: test invalid models.


@pytest.mark.asyncio
async def test_responses_endpoint(
    key_client: TestClient,
    responses_api: LLMModel,
    normal_user: BackendUser,
    mock_repositories: Repositories,
    usage_service: UsageService,
) -> None:
    request: dict[str, Any] = {
        "input": [
            {"role": "system", "content": "whatever"},
            {"role": "user", "content": "whatever more"},
        ],
        "model": responses_api.model.model.id,
    }

    CreateResponse.model_validate(request)
    # Make sure no usage happened yet
    balance = await usage_service.get_current_user_balance(normal_user.id)
    assert balance.balance_used == 0
    response = key_client.post("/api/v1/responses", json=request)
    result = response.json()
    assert response.status_code == 200
    assert "output" in result
    assert "usage" in result
    assert result["usage"]["input_tokens"] == 36
    usage = ResponseUsage.model_validate(result["usage"])
    balance = await usage_service.get_current_user_balance(normal_user.id)
    cost = responses_api.calc_cost_from_response_usage(usage)
    assert balance.balance_used == pytest.approx(cost)
    assert balance.balance_used > 0
    # use a streamig response
    request["stream"] = True
    response = key_client.post("/api/v1/responses", json=request)
    async for token in response.aiter_text():
        print(token)
        # Lets check, that the format fits.
        event_match = re.search(r"^event:\s*(\S+)", token, re.MULTILINE)
        assert not event_match is None
        # Extract data line
        data_match = re.search(r"^data:\s*(\{.*\})", token, re.MULTILINE)
        assert not data_match is None

    new_balance = await usage_service.get_current_user_balance(normal_user.id)
    assert new_balance.balance_used > balance.balance_used
    # TODO: Invalid models and actual stream cost calculation.

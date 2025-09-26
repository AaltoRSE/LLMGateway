import re
from typing import Any, AsyncIterator, List
from datetime import datetime
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.services.usage_service import (
    UsageService,
    APIRequest,
    RequestSource,
    UserAndKeyUsageData,
)
from app.services.model_service import ModelService
from app.services.session_service import SessionService, SessionAuthData
from app.services.user_service import UserService, UserBase, User
from app.services.key_service import KeyService, APIKey
from app.responses.self_service import UsageResponse
from tests.fixtures.db_fixtures import Repositories
from app.security.auth import BackendUser
from app.utils.llm_model import LLMModel
from app.requests.self_service_requests import *
from app.responses.auth import AuthInfo
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
async def test_create_key(
    normal_session_client: TestClient,
    key_service: KeyService,
) -> None:
    request = CreateKeyRequest(name="TestKey")
    response = normal_session_client.post(
        "/selfservice/createkey", json=request.model_dump()
    )
    assert response.status_code == 201
    new_key = APIKey.model_validate(response.json())
    key = await key_service.get_user_key_if_active(new_key.key)
    assert new_key.model_dump() == key.model_dump()


@pytest.mark.asyncio
async def test_delete_key(
    normal_session_client: TestClient,
    key_service: KeyService,
    user_service: UserService,
) -> None:
    request = CreateKeyRequest(name="TestKey")
    response = normal_session_client.post(
        "/selfservice/createkey", json=request.model_dump()
    )
    assert response.status_code == 201
    new_key = APIKey.model_validate(response.json())
    key = await key_service.get_user_key_if_active(new_key.key)
    assert new_key.model_dump() == key.model_dump()

    user = await user_service.create_new_user(
        UserBase(
            accepted_agreement_version="1.0",
            admin=False,
            first_name="Test",
            last_name="Test",
            auth_id="ExistingUser",
        )
    )
    other_key = await key_service.create_key("Test", user_id=user.id)
    service_key = await key_service.create_key("Test", service="TestService")
    delete_request = DeleteKeyRequest(key=other_key.key)
    response = normal_session_client.post(
        "/selfservice/deletekey", json=delete_request.model_dump()
    )
    assert response.status_code == 404
    delete_request.key = service_key.key
    response = normal_session_client.post(
        "/selfservice/deletekey", json=delete_request.model_dump()
    )
    assert response.status_code == 404
    delete_request.key = new_key.key
    response = normal_session_client.post(
        "/selfservice/deletekey", json=delete_request.model_dump()
    )
    assert response.status_code == 200
    key = await key_service.get_user_key_if_active(new_key.key)
    assert key is None


@pytest.mark.asyncio
async def test_get_keys(
    normal_session_client: TestClient,
    normal_user: User,
    key_service: KeyService,
    user_service: UserService,
) -> None:
    request = CreateKeyRequest(name="TestKey")
    response = normal_session_client.post(
        "/selfservice/createkey", json=request.model_dump()
    )
    assert response.status_code == 201
    new_key = APIKey.model_validate(response.json())
    key = await key_service.get_user_key_if_active(new_key.key)
    assert new_key.model_dump() == key.model_dump()

    user = await user_service.create_new_user(
        UserBase(
            accepted_agreement_version="1.0",
            admin=False,
            first_name="Test",
            last_name="Test",
            auth_id="ExistingUser",
        )
    )
    other_key = await key_service.create_key("Test", user_id=user.id)
    service_key = await key_service.create_key("Test", service="TestService")
    second_key = await key_service.create_key("Test2", user_id=normal_user.id)

    response = normal_session_client.post("/selfservice/getkeys")
    assert response.status_code == 200
    data = [APIKey.model_validate(key) for key in response.json()]
    assert len(data) == 2
    assert second_key.key in [elem.key for elem in data]
    assert not (service_key.key in [elem.key for elem in data])
    assert not (other_key.key in [elem.key for elem in data])


@pytest.mark.asyncio
async def test_get_usage_details(
    normal_session_client: TestClient,
    normal_user: BackendUser,
    usage_service: UsageService,
) -> None:
    # Make sure no usage happened yet
    balance = await usage_service.get_current_user_balance(normal_user.id)
    assert balance.balance_used == 0
    response = normal_session_client.post("/selfservice/usage_details", json={})
    result = response.json()
    assert len(result) == 0
    await usage_service.log_usage(
        RequestSource(user_id=normal_user.id),
        APIRequest(
            prompt_tokens=10,
            completion_tokens=10,
            cost=3,
            model="Test",
            timestamp=datetime.now(),
        ),
    )
    response = normal_session_client.post("/selfservice/usage_details", json={})
    print(response.json())
    usage = [APIRequest.model_validate(request) for request in response.json()]
    assert len(usage) == 1
    await usage_service.log_usage(
        RequestSource(user_id=normal_user.id),
        APIRequest(
            prompt_tokens=11,
            completion_tokens=11,
            cost=1,
            model="Test",
            timestamp=datetime.now(),
        ),
    )
    response = normal_session_client.post("/selfservice/usage_details", json={})
    usage = [APIRequest.model_validate(request) for request in response.json()]
    assert len(usage) == 2


@pytest.mark.asyncio
async def test_accept_agreement(
    normal_session_client: TestClient,
    normal_user: User,
    user_service: UserService,
    session_service: SessionService,
    llm_gateway: FastAPI,
) -> None:
    from app.config import app_configuration

    session = await session_service.create_session(
        SessionAuthData(
            auth_id=normal_user.auth_id,
            first_name=normal_user.first_name,
            last_name=normal_user.last_name,
            roles=["employee"],
        ),
        source_ip="test",
        user_service=user_service,
    )
    from app.security.session import get_session

    def return_session():
        return session

    # We need to mock the get_session functionality.
    llm_gateway.dependency_overrides[get_session] = return_session
    user = await user_service.get_user_by_id(normal_user.id)
    assert (
        user.accepted_agreement_version != app_configuration.current_agreement_version
    )
    response = normal_session_client.post("/selfservice/accept_agreement", json={})
    print(response.json())
    assert response.status_code == 200
    user = await user_service.get_user_by_id(normal_user.id)
    assert (
        user.accepted_agreement_version == app_configuration.current_agreement_version
    )


@pytest.mark.asyncio
async def test_get_usage(
    normal_session_client: TestClient,
    normal_user: User,
    admin_user: User,
    usage_service: UsageService,
    key_service: KeyService,
    mock_repositories: Repositories,
) -> None:
    # Make sure no usage happened yet
    response = normal_session_client.post("/selfservice/usage", json={})
    usage_data = UsageResponse.model_validate(response.json())
    assert usage_data.usage.completion_tokens == 0
    assert usage_data.usage.cost == 0
    assert usage_data.usage.prompt_tokens == 0
    assert usage_data.balance == 0
    # We are nto asserting a quota here...
    assert len(usage_data.key_details) == 0
    key1 = await key_service.create_key("TestKey", user_id=normal_user.id)
    key2 = await key_service.create_key("TestKey2", user_id=normal_user.id)
    key3 = await key_service.create_key("TestKey3", user_id=admin_user.id)
    response = normal_session_client.post("/selfservice/usage", json={})
    usage_data = UsageResponse.model_validate(response.json())
    assert usage_data.usage.completion_tokens == 0
    assert usage_data.usage.cost == 0
    assert usage_data.usage.prompt_tokens == 0
    # Now there are 2 keys
    assert len(usage_data.key_details) == 2

    await usage_service.log_usage(
        RequestSource(user_id=normal_user.id, key=key1.key),
        APIRequest(
            prompt_tokens=10,
            completion_tokens=10,
            cost=3,
            model="Test",
            timestamp=datetime.now(),
        ),
    )
    await usage_service.log_usage(
        RequestSource(user_id=normal_user.id, key=key2.key),
        APIRequest(
            prompt_tokens=20,
            completion_tokens=15,
            cost=2,
            model="Test",
            timestamp=datetime.now(),
        ),
    )

    # This does not go through the service, as the service assumes all logs to be
    # current
    await mock_repositories.usage_repo.log_usage(
        source=RequestSource(user_id=normal_user.id, key=key2.key),
        usage=APIRequest(
            prompt_tokens=30,
            completion_tokens=20,
            cost=1,
            model="Test",
            timestamp=datetime.fromtimestamp(0),
        ),
    )
    await usage_service.log_usage(
        RequestSource(user_id=admin_user.id, key=key3.key),
        APIRequest(
            prompt_tokens=20,
            completion_tokens=15,
            cost=2,
            model="Test",
            timestamp=datetime.now(),
        ),
    )
    response = normal_session_client.post("/selfservice/usage", json={})
    usage_data = UsageResponse.model_validate(response.json())
    assert usage_data.usage.completion_tokens == 45
    assert usage_data.usage.cost == 6
    assert usage_data.usage.prompt_tokens == 60
    assert usage_data.balance == 5  # This is only the recent usage
    assert len(usage_data.key_details) == 2
    key1_data = usage_data.key_details[0]
    key2_data = usage_data.key_details[1]
    if usage_data.key_details[0].key == key2.key:
        key1_data = usage_data.key_details[1]
        key2_data = usage_data.key_details[0]
    assert key1_data.quota == key1.quota
    assert key1_data.current_completion_tokens == 10
    assert key1_data.current_prompt_tokens == 10
    assert key1_data.current_cost == 3
    assert key1_data.total_completion_tokens == 10
    assert key1_data.total_prompt_tokens == 10
    assert key1_data.total_cost == 3
    assert key2_data.quota == key2.quota
    assert key2_data.current_completion_tokens == 15
    assert key2_data.current_prompt_tokens == 20
    assert key2_data.current_cost == 2
    assert key2_data.total_completion_tokens == 35
    assert key2_data.total_prompt_tokens == 50
    assert key2_data.total_cost == 3

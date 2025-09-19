from datetime import datetime

import pytest
import random
import respx
import json

from requests import PreparedRequest

from typing import Any, List, Dict, Generator, AsyncGenerator
from httpx import Request, Response, AsyncByteStream
from sse_starlette.sse import EventSourceResponse

from app.services.model_service import ModelService
from app.utils.llm_model import (
    ChatCompletionResponse,
    ChatCompletionRequest,
    CreateResponse,
    LLMModel,
)
from app.schemas.llmmodel_schema import LLMModelData, LLMModelDataDetails, model_types
from app.schemas.openai_schemas import (
    OutputMessage,
    Response1 as OpenAIResponse,
    ReasoningItem,
    ResponseCreatedEvent,
    ResponseUsage,
    ResponseInProgressEvent,
    OutputTokensDetails,
    InputTokensDetails1,
)


class AsyncGeneratorByteStream(AsyncByteStream):
    def __init__(self, generator: AsyncGenerator[bytes, None]):
        self.generator = generator

    async def __aiter__(self):
        async for chunk in self.generator:
            yield chunk


def completions_get_default_answer(model: str) -> ChatCompletionResponse:
    """Returns a default answer for the LLM API."""
    return ChatCompletionResponse.model_validate(
        {
            "id": "chatcmpl-B9MHDbslfkBeAs8l4bebGdFOJ6PeG",
            "object": "chat.completion",
            "created": 1741570283,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "The image shows a wooden boardwalk path running through a lush green field or meadow. The sky is bright blue with some scattered clouds, giving the scene a serene and peaceful atmosphere. Trees and shrubs are visible in the background.",
                        "refusal": None,
                        "annotations": [],
                    },
                    "logprobs": None,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 1117,
                "completion_tokens": 46,
                "total_tokens": 1163,
                "prompt_tokens_details": {"cached_tokens": 0, "audio_tokens": 0},
                "completion_tokens_details": {
                    "reasoning_tokens": 0,
                    "audio_tokens": 0,
                    "accepted_prediction_tokens": 0,
                    "rejected_prediction_tokens": 0,
                },
            },
            "service_tier": "default",
            "system_fingerprint": "fp_fc9f1d7035",
        }
    )


def completions_build_chunk(
    model: str, choices: List[Any], usage: None | dict[str, Any] = None
) -> bytes:
    data: dict[str, Any] = {
        "id": "chatcmpl-123",
        "object": "chat.completion.chunk",
        "created": 1694268190,
        "model": model,
        "system_fingerprint": "fp_44709d6fcb",
        "choices": choices,
    }
    if not usage is None:
        data["usage"] = usage
    return f"data: {json.dumps(data)}".encode("utf-8")


def completions_create_chunk(model: str) -> Dict[str, Any]:
    return {
        "id": f"chunk-{model}-{random.randint(1, 1000)}",
        "object": "chat.completion.chunk",
        "created": int(datetime.now().timestamp()),
        "model": model,
        "system_fingerprint": "TestCase",
        "choices": [
            {
                "index": 0,
                "delta": {"role": "assistant", "content": "This is a test chunk."},
                "logprobs": None,
                "finish_reason": None,
            }
        ],
    }


def completions_finish_chunk(model: str) -> Dict[str, Any]:
    return {
        "id": f"chunk-{model}-{random.randint(1, 1000)}",
        "object": "chat.completion.chunk",
        "created": int(datetime.now().timestamp()),
        "model": model,
        "system_fingerprint": "TestCase",
        "choices": [{"index": 0, "delta": {}, "logprobs": None, "finish_reason": None}],
    }


def completions_usage_chunk(model: str) -> Dict[str, Any]:
    return {
        "id": f"chunk-{model}-{random.randint(1, 1000)}",
        "object": "chat.completion.chunk",
        "created": int(datetime.now().timestamp()),
        "model": model,
        "system_fingerprint": "TestCase",
        "choices": [
            {"index": 0, "delta": {}, "logprobs": None, "finish_reason": "stop"}
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "prompt_tokens_details": {"cached_tokens": 3, "audio_tokens": 0},
            "completion_tokens_details": {
                "reasoning_tokens": 0,
                "audio_tokens": 0,
                "accepted_prediction_tokens": 0,
                "rejected_prediction_tokens": 0,
            },
        },
    }


async def completions_get_streaming_response(
    model: str, include_usage: bool
) -> AsyncGenerator[bytes, None]:
    yield completions_build_chunk(
        model,
        [
            {
                "index": 0,
                "delta": {"role": "assistant", "content": ""},
                "logprobs": None,
                "finish_reason": None,
            }
        ],
    )
    yield completions_build_chunk(
        model,
        [
            {
                "index": 0,
                "delta": {"content": "Hello"},
                "logprobs": None,
                "finish_reason": None,
            }
        ],
    )
    if include_usage:
        yield completions_build_chunk(
            model,
            [],
            {
                "completion_tokens": 2,
                "prompt_tokens": 2,
                "total_tokens": 4,
                "prompt_tokens_details": {"cached_tokens": 1},
            },
        )
    yield completions_build_chunk(
        model, [{"index": 0, "delta": {}, "logprobs": None, "finish_reason": "stop"}]
    )


def completions_response(request: PreparedRequest | Request) -> Response:
    httpx_request = isinstance(request, Request)
    if httpx_request:
        body = request.content.decode("utf-8")
    else:
        body = request.body
        assert isinstance(body, str)
    data = ChatCompletionRequest.model_validate_json(body)
    model = data.model
    assert isinstance(model, str)
    if data.stream:
        include_stream_usage = (
            data.stream_options.include_usage
            if not data.stream_options is None
            else False
        )
        include_stream_usage = (
            False if include_stream_usage is None else include_stream_usage
        )
        return Response(
            stream=AsyncGeneratorByteStream(
                completions_get_streaming_response(model, include_stream_usage)
            ),
            status_code=200,
            headers={"content-type": "text/event-stream"},
        )
    else:
        response = ChatCompletionResponse.model_validate(
            completions_get_default_answer(model)
        )
        return Response(
            content=json.dumps(response.model_dump()),
            headers={"Content-Type": "application/json"},
            status_code=200,
        )


@pytest.fixture
def completions_api() -> Generator[respx.MockRouter, Any, Any]:
    """
    Fixture for an LLM endpoint which yields a response with only ones as
    the embedding vector
    """
    with respx.mock as mock:
        call_url = f"http://llm.service.com/chat/completions"
        print(f"Mocking calls to {call_url}")
        mock.post(
            call_url,
        ).mock(side_effect=completions_response)
        yield mock


### Responses Data ###

responses_default_reasoning_item = ReasoningItem.model_validate(
    {
        "id": "rs_68ad65d54c2c81908586381974845116027c9e39912d5273",
        "type": "reasoning",
        "summary": [{"type": "summary_text", "text": "Some reasoning text"}],
    }
)
responses_default_output_item = OutputMessage.model_validate(
    {
        "id": "msg_68ad65d7157c8190a971b4b96c934a7b027c9e39912d5273",
        "type": "message",
        "status": "completed",
        "content": [
            {"type": "output_text", "annotations": [], "text": "Some output text"}
        ],
        "role": "assistant",
    }
)


responses_default_usage = ResponseUsage(
    input_tokens=20,
    input_tokens_details=InputTokensDetails1(cached_tokens=1),
    output_tokens=20,
    output_tokens_details=OutputTokensDetails(reasoning_tokens=10),
    total_tokens=40,
)
responses_default_response_json: Dict[str, Any] = {
    "id": "resp_68ad65d4e4108190b787ee8780518c90027c9e39912d5273",
    "object": "response",
    "created_at": 1756194260,
    "status": "in_progress",
    "background": False,
    "content_filters": None,
    "error": None,
    "incomplete_details": None,
    "instructions": "You are a helpful assistant",
    "max_output_tokens": 2048,
    "max_tool_calls": None,
    "model": "gpt-5-aaltogpt",
    "output": [],
    "parallel_tool_calls": True,
    "previous_response_id": None,
    "prompt_cache_key": None,
    "reasoning": {"effort": "low", "summary": "detailed"},
    "safety_identifier": None,
    "service_tier": "auto",
    "store": None,
    "temperature": 1.0,
    "text": {"format": {"type": "text"}},
    "tool_choice": "auto",
    "tools": [],
    "top_p": 1.0,
    "truncation": "disabled",
    "usage": None,
    "user": None,
    "metadata": {},
}

responses_default_response = OpenAIResponse.model_validate(
    responses_default_response_json
)


def responses_get_default_answer(model: str) -> OpenAIResponse:
    return OpenAIResponse.model_validate(
        {
            "id": "resp_67ccd2bed1ec8190b14f964abc0542670bb6a6b452d3795b",
            "object": "response",
            "created_at": 1741476542,
            "status": "completed",
            "error": None,
            "incomplete_details": None,
            "instructions": None,
            "max_output_tokens": None,
            "model": model,
            "output": [
                {
                    "type": "message",
                    "id": "msg_67ccd2bf17f0819081ff3bb2cf6508e60bb6a6b452d3795b",
                    "status": "completed",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "In a peaceful grove beneath a silver moon, a unicorn named Lumina discovered a hidden pool that reflected the stars. As she dipped her horn into the water, the pool began to shimmer, revealing a pathway to a magical realm of endless night skies. Filled with wonder, Lumina whispered a wish for all who dream to find their own hidden magic, and as she glanced back, her hoofprints sparkled like stardust.",
                            "annotations": [],
                        }
                    ],
                }
            ],
            "parallel_tool_calls": True,
            "previous_response_id": None,
            "reasoning": {"effort": None, "summary": None},
            "store": True,
            "temperature": 1.0,
            "text": {"format": {"type": "text"}},
            "tool_choice": "auto",
            "tools": [],
            "top_p": 1.0,
            "truncation": "disabled",
            "usage": {
                "input_tokens": 36,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens": 87,
                "output_tokens_details": {"reasoning_tokens": 0},
                "total_tokens": 123,
            },
            "user": None,
            "metadata": {},
        }
    )


def responses_build_chunk(
    type: str,
    content: str | None = None,
    usage: ResponseUsage | None = None,
    reset_items: bool = False,
    addedItem: ReasoningItem | OutputMessage | None = None,
) -> bytes:

    chunk = f"event: {type}\n"
    match type:
        case "response.created":
            chunk += f"data : {'{' + ResponseCreatedEvent(type='response.created', response=responses_default_response).model_dump_json() + '}'}"
            # Handle response.created
        case "response.in_progress":
            chunk += f"data : {'{' + ResponseInProgressEvent(type='response.in_progress', response=responses_default_response).model_dump_json() + '}'}"
        case "response.output_item.added":
            assert not addedItem is None
            item = (
                '{"type":"response.output_item.added","sequence_number":2,"output_index":0,"item": {'
                + addedItem.model_dump_json()
                + "}}"
            )
            chunk += f"data : {item}"
            # Handle response.output_item.added
        case "response.reasoning_summary_part.added":
            item = '"type":"response.reasoning_summary_part.added","sequence_number":3,"item_id":"rs_68ad65d54c2c81908586381974845116027c9e39912d5273","output_index":0,"summary_index":0,"part": {"type":"summary_text","text":""}'
            chunk += f"data: {'{' + item + '}'}"
        case "response.reasoning_summary_text.delta":
            assert not content is None
            # We will for this mock, ignore that there is only one sequence number...
            item = f'"type":"response.reasoning_summary_text.delta","sequence_number":4,"item_id":"rs_68ad65d54c2c81908586381974845116027c9e39912d5273","output_index":0,"summary_index":0,"delta":"{content}"'
            chunk += f"data: {'{' + item + '}'}"
        case "response.reasoning_summary_text.done":
            assert not content is None
            item = f'"type":"response.reasoning_summary_text.done","sequence_number":79,"item_id":"rs_68ad65d54c2c81908586381974845116027c9e39912d5273","output_index":0,"summary_index":0,"text":"{content}"'
            chunk += f"data: {'{' + item + '}'}"
        case "response.reasoning_summary_part.done":
            item = '"type":"response.reasoning_summary_part.done","sequence_number":80,"item_id":"rs_68ad65d54c2c81908586381974845116027c9e39912d5273","output_index":0,"summary_index":0,"part":{"type":"summary_text","text":"Reasoning Text"}'
            chunk += f"data: {'{' + item + '}'}"
        case "response.output_item.done":
            assert not addedItem is None
            item = f'"type":"response.output_item.done","sequence_number":81,"output_index":0,"item":{addedItem.model_dump_json()}'
            chunk += f"data: {'{' + item + '}'}"
        case "response.content_part.added":
            item = '"type":"response.content_part.added","sequence_number":83,"item_id":"msg_68ad65d7157c8190a971b4b96c934a7b027c9e39912d5273","output_index":1,"content_index":0,"part":{"type":"output_text","annotations":[],"text":""}'
            chunk += f"data: {'{' + item + '}'}"
        case "response.output_text.delta":
            assert not content is None
            item = f'"type":"response.output_text.delta","sequence_number":87,"item_id":"msg_68ad65d7157c8190a971b4b96c934a7b027c9e39912d5273","output_index":1,"content_index":0,"delta":"{ content }"'
            chunk += f"data: {'{' + item + '}'}"
        case "response.output_text.done":
            assert not content is None
            item = f'"type":"response.output_text.done","sequence_number":97,"item_id":"msg_68ad65d7157c8190a971b4b96c934a7b027c9e39912d5273","output_index":1,"content_index":0,"text":"{ content} "'
            chunk += f"data: {'{' + item + '}'}"
        case "response.content_part.done":
            item = '"type":"response.content_part.done","sequence_number":98,"item_id":"msg_68ad65d7157c8190a971b4b96c934a7b027c9e39912d5273","output_index":1,"content_index":0,"part":{"type":"output_text","annotations":[],"text":"Part text"}}'
            chunk += f"data: {'{' + item + '}'}"
        case "response.completed":
            assert not content is None
            assert not usage is None
            response = responses_default_response.model_copy(deep=True)
            response.usage = usage
            response = response.model_dump()
            response["output"].append(
                {
                    "id": "rs_68ad65d54c2c81908586381974845116027c9e39912d5273",
                    "type": "reasoning",
                    "summary": [],
                }
            )
            response["output"].append(
                {
                    "id": "msg_68ad65d7157c8190a971b4b96c934a7b027c9e39912d5273",
                    "type": "message",
                    "status": "completed",
                    "content": [
                        {"type": "output_text", "annotations": [], "text": content}
                    ],
                    "role": "assistant",
                }
            )
            data = (
                '{ "type": "response.completed", "response":'
                + json.dumps(response)
                + ', "sequence_number": 1}'
            )
            chunk += f"data: { data }"
        case _:
            # Unknown type
            pass
    return chunk.encode("utf-8")


async def responses_get_streaming_response(
    model: str,
) -> AsyncGenerator[bytes, None]:

    yield responses_build_chunk(type="response.created")
    yield responses_build_chunk(type="response.in_progress")
    yield responses_build_chunk(
        type="response.item_added", addedItem=responses_default_reasoning_item
    )
    yield responses_build_chunk(type="response.reasoning_summary_part.added")
    yield responses_build_chunk(
        type="response.reasoning_summary_text.delta", content="Test"
    )
    yield responses_build_chunk(
        type="response.reasoning_summary_text.delta", content=" more test"
    )
    yield responses_build_chunk(
        type="response.reasoning_summary_text.done",
        content="reasoning",
    )
    yield responses_build_chunk(
        type="response.reasoning_summary_part.done",
        addedItem=responses_default_reasoning_item,
    )
    yield responses_build_chunk(
        type="response.output_item.done", addedItem=responses_default_reasoning_item
    )
    yield responses_build_chunk(
        type="response.output_item.added", addedItem=responses_default_output_item
    )
    yield responses_build_chunk(type="response.content_part.added")
    yield responses_build_chunk(type="response.output_text.delta", content="Some")
    yield responses_build_chunk(type="response.output_text.delta", content=" content")
    yield responses_build_chunk(
        type="response.output_text.done", content="Some content"
    )
    yield responses_build_chunk(
        type="response.content_part.done", addedItem=responses_default_output_item
    )
    yield responses_build_chunk(
        type="response.completed",
        content="Some content",
        usage=responses_default_usage,
    )


def responses_response(request: PreparedRequest | Request) -> Response:
    httpx_request = isinstance(request, Request)
    if httpx_request:
        body = request.content.decode("utf-8")
    else:
        body = request.body
        assert isinstance(body, str)
    data = CreateResponse.model_validate_json(body)
    model = data.model
    assert isinstance(model, str)
    if data.stream:
        return Response(
            stream=AsyncGeneratorByteStream(responses_get_streaming_response(model)),
            status_code=200,
            headers={"content-type": "text/event-stream"},
        )
    else:
        response = responses_get_default_answer(model)
        return Response(
            content=json.dumps(response.model_dump()),
            headers={"Content-Type": "application/json"},
            status_code=200,
        )


@pytest.fixture
async def responses_api(
    response_model: LLMModel,
) -> AsyncGenerator[LLMModel, Any]:
    """
    Fixture for an LLM endpoint which yields a response with only ones as
    the embedding vector
    """

    with respx.mock as mock:
        call_url = f"{response_model.model.host}{response_model.model.path}"
        print(f"Mocking calls to {call_url}")
        mock.post(
            call_url,
        ).mock(side_effect=responses_response)
        yield response_model


@pytest.fixture
async def response_model(
    model_service: ModelService,
) -> AsyncGenerator[LLMModel, Any]:
    model = LLMModelData(
        cached_token_cost=0.001,
        prompt_cost=0.001,
        description="TestModel",
        completion_cost=0.001,
        host="http://llm.service.com",
        path="/responses",
        name="testmodel",
        model=LLMModelDataDetails(
            id="responses", owned_by="Admin", permissions=[], type=["responses"]
        ),
    )

    await model_service.add_model(model)
    yield await model_service.get_model(model.model.id)


@pytest.fixture
async def general_api(general_model: LLMModel) -> AsyncGenerator[LLMModelData, Any]:
    """
    Fixture for an LLM endpoint which yields a response with only ones as
    the embedding vector
    """

    with respx.mock as mock:
        call_url = f"{general_model.model.host}{general_model.model.path}"
        print(f"Mocking calls to {call_url}")
        mock.post(
            call_url,
        ).mock(side_effect=responses_response)
    yield general_model


@pytest.fixture
async def general_model(
    model_service: ModelService,
) -> AsyncGenerator[LLMModel, Any]:
    model = LLMModel(
        LLMModelData(
            cached_token_cost=0.001,
            prompt_cost=0.001,
            description="TestModel",
            completion_cost=0.001,
            host="http://llm.service.com",
            path="/general",
            name="testmodel",
            model=LLMModelDataDetails(
                id="general",
                owned_by="Admin",
                permissions=[],
                type=["chat", "responses", "embedding"],
            ),
        )
    )
    await model_service.add_model(model)
    yield await model_service.get_model(model.model.id)


@pytest.fixture
async def embedding_api(
    embedding_model: LLMModel,
) -> AsyncGenerator[LLMModel, Any]:
    """
    Fixture for an LLM endpoint which yields a response with only ones as
    the embedding vector
    """

    with respx.mock as mock:
        call_url = f"{embedding_model.model.host}{embedding_model.model.path}"
        print(f"Mocking calls to {call_url}")
        mock.post(
            call_url,
        ).mock(side_effect=responses_response)
    yield embedding_model


@pytest.fixture
async def embedding_model(
    model_service: ModelService,
) -> AsyncGenerator[LLMModel, Any]:
    model = LLMModelData(
        cached_token_cost=0.001,
        prompt_cost=0.001,
        description="TestModel",
        completion_cost=0.001,
        host="http://llm.service.com",
        path="/embedding",
        name="testmodel",
        model=LLMModelDataDetails(
            id="embedding", owned_by="Admin", permissions=[], type=["embedding"]
        ),
    )

    await model_service.add_model(model)
    yield await model_service.get_model(model.model.id)

import responses
import pytest
import random
import respx
import json
from httpx import Request, Response

from requests import PreparedRequest
from typing import Tuple, Dict, Optional, Generator, Any
from pydantic import BaseModel, Field

from fastapi import UploadFile
from io import BytesIO
from starlette.datastructures import Headers


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str
    encoding_format: str = Field(default="float")
    dimensions: int = Field(default=512)
    user: Optional[str] = None


class Embedding(BaseModel):
    object: Optional[str] = "embedding"
    embedding: list[float] | list[str]
    index: Optional[int] = 0


class Usage(BaseModel):
    prompt_tokens: Optional[int] = 1
    total_tokens: Optional[int] = 1


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[Embedding]
    model: str
    usage: Usage


import os
import base64


def generate_random_base64(length: int) -> str:
    # Generate random bytes
    random_bytes = os.urandom(length)
    # Encode the bytes to a Base64 string
    base64_string = base64.b64encode(random_bytes).decode("utf-8")
    return base64_string


def mock_embedding(
    dimension: int, encoding_format: str, model: str, fixed_value: float | None = None
) -> Embedding:
    vector = (
        [random.random() for _ in range(dimension)]
        if fixed_value is None
        else [fixed_value] * dimension
    )
    return Embedding(embedding=vector)


def embedding_response(
    request: PreparedRequest | Request, fixed_value: float | None = None
) -> Tuple[int, Dict[str, str], str] | Response:
    httpx_request = isinstance(request, Request)
    if httpx_request:
        body = request.content.decode("utf-8")
    else:
        body = request.body
    try:
        assert isinstance(body, str)
        try:
            embedding_request = EmbeddingRequest.model_validate(json.loads(body))
        except Exception as e:
            print(e)

        embedding_request = EmbeddingRequest.model_validate(json.loads(body))
        auth_header = request.headers["Authorization"]
        assert not auth_header is None
        if isinstance(embedding_request.input, list):
            embeddings = [
                mock_embedding(
                    embedding_request.dimensions,
                    embedding_request.encoding_format,
                    embedding_request.model,
                    fixed_value,
                )
                for _ in range(len(embedding_request.input))
            ]
        else:
            embeddings = [
                mock_embedding(
                    embedding_request.dimensions,
                    embedding_request.encoding_format,
                    embedding_request.model,
                    fixed_value,
                )
            ]
        response = EmbeddingResponse(
            data=embeddings, model=embedding_request.model, usage=Usage()
        )
        if httpx_request:
            return Response(200, content=response.model_dump_json())
        return (200, {}, response.model_dump_json())

    except Exception as e:
        if httpx_request:
            return Response(400, content=str(e))
        return (400, {}, str(e))


def requests_response(request: PreparedRequest) -> Tuple[int, Dict[str, str], str]:
    response = embedding_response(request)
    assert isinstance(response, tuple)
    return response


def httpx_response(request: Request) -> Response:
    response = embedding_response(request)
    assert isinstance(response, Response)
    return response


def requests_response_fixed(
    request: PreparedRequest,
) -> Tuple[int, Dict[str, str], str]:
    response = embedding_response(request, 1.0)
    assert isinstance(response, tuple)
    return response


def httpx_response_fixed(request: Request) -> Response:
    response = embedding_response(request, 1.0)
    assert isinstance(response, Response)
    return response


@pytest.fixture
def embedding_api() -> Generator[respx.MockRouter, Any, Any]:
    with respx.mock as mock:

        call_url = f"http://embedding.host.com/v1/embeddings"
        print(f"Mocking calls to {call_url}")
        responses.add_callback(
            responses.POST,
            call_url,
            callback=requests_response,
            content_type="application/json",
        )
        mock.post(
            call_url,
        ).mock(side_effect=httpx_response)
        yield mock


@pytest.fixture
def embedding_api_fixed() -> Generator[respx.MockRouter, Any, Any]:
    """
    Fixture for an embedding endpoint which yields a response with only ones as
    the embedding vector
    """
    with respx.mock as mock:        
        call_url = f"http://embedding.host.com/v1/embeddings"
        print(f"Mocking calls to {call_url}")
        responses.add_callback(
            responses.POST,
            call_url,
            callback=requests_response_fixed,
            content_type="application/json",
        )
        mock.post(
            call_url,
        ).mock(side_effect=httpx_response_fixed)
        yield mock

from fastapi.security import APIKeyHeader
from fastapi import FastAPI, Request, BackgroundTasks, Security, HTTPException
from fastapi import status


from contextlib import asynccontextmanager

import logging
import re
import os

from .llama_requests import (
    CompletionRequest,
    ChatCompletionRequest,
    EmbeddingRequest,
)


api_key_header = APIKeyHeader(name="Authorization")
admin_key_header = APIKeyHeader(name="AdminKey")

logger = logging.getLogger(__name__)


def get_admin_key(admin_key_header: str = Security(admin_key_header)) -> str:
    if admin_key_header == os.environ.get("ADMIN_KEY"):
        return admin_key_header
    raise HTTPException(
        status_code=401,
        detail="Priviledged Access required",
    )


# Need to figure out how to offer two alternative authentication methods...
def get_api_key(key_handler, api_key_header: str = Security(api_key_header)) -> str:
    api_key = re.sub("^Bearer ", "", api_key_header)
    if key_handler.check_key(api_key):
        return api_key
    else:
        logger.info(api_key_header)
        logger.info(api_key)
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API Key",
    )


def parse_body(data: CompletionRequest | ChatCompletionRequest | EmbeddingRequest):
    # Extract data from request body
    # Replace this with your logic to extract data from the request body
    try:
        model = model_handler.get_model_path(data.model)
    except KeyError as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Requested Model not available"
        )
    stream = data.stream
    return model, stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    stream_client = httpx.AsyncClient(base_url="https://llm.k8s-test.cs.aalto.fi")
    yield
    # Clean up the ML models and release the resources
    await stream_client.aclose()


def log_streamed_usage():
    pass


def log_non_streamed_usage(sourcetype, source, model, responseData):
    tokens = responseData["usage"]["total_tokens"]
    if sourcetype == "apikey":
        logger.log_usage_for_key(tokens, model, source)
    else:
        logger.log_usage_for_user(tokens, model, source)

"""
A placeholder hello world app.
"""

from typing import Union
from functools import partial

from fastapi import FastAPI, Request, BackgroundTasks, Security, HTTPException
from fastapi.security import APIKeyHeader

import httpx
import logging
import re

from starlette.datastructures import MutableHeaders

from contextlib import asynccontextmanager

from utils.requests import CompletionRequest, ChatCompletionRequest, EmbeddingRequest
from utils.responses import LoggingStreamResponse, event_generator
from utils.stream_logger import StreamLogger
from utils.logging_handler import LoggingHandler
from utils.key_handler import KeyHandler


key_handler = KeyHandler()

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
uvlogger = logging.getLogger(__name__)

infernence_apikey = "Bearer 123"
availablemodels = {"llama2-7b": "llama2", "llama2-7b-chat": "llama2-7b-chat"}
logger = LoggingHandler()
stream_client = httpx.AsyncClient(base_url="https://llm.k8s-test.cs.aalto.fi")
api_key_header = APIKeyHeader(name="Authorization")


# Need to figure out how to offer two alternative authentication methods...
def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    api_key = re.sub("^Bearer ", "", api_key_header)
    if key_handler.check_key(api_key):
        return api_key
    else:
        uvlogger.info(api_key_header)
        uvlogger.info(api_key)
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API Key",
    )


def parse_body(data: CompletionRequest | ChatCompletionRequest | EmbeddingRequest):
    # Extract data from request body
    # Replace this with your logic to extract data from the request body
    model = availablemodels[data.model]
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


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


async def build_request(
    requestData: ChatCompletionRequest,
    headers: MutableHeaders,
    path: str,
    method: str,
    body: str,
):
    model, stream = parse_body(requestData)
    uvlogger.info("Got Request")
    # Update the request path
    # TODO: Need to handle model not found error!
    url = httpx.URL(path=model + path)
    # Add the API Key for the inference server
    headers["Authorization"] = infernence_apikey
    headers["host"] = "llm.k8s-test.cs.aalto.fi"
    # extract the body for forwarding.
    req = stream_client.build_request(
        method,
        url,
        headers=headers,
        content=body,
        timeout=300.0,
    )

    return req, model, stream


@app.post("/v1/completions")
async def infer(
    requestData: CompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
):
    content = await request.body()
    req, model, stream = await build_request(
        requestData,
        request.headers.mutablecopy(),
        request.url.path,
        request.method,
        content.decode(),
    )
    if stream:
        responselogger = StreamLogger(
            logging_handler=logger, source=api_key, iskey=True, model=model
        )
        # no logging implemented yet...
        r = await stream_client.send(req, stream=True)
        background_tasks.add_task(r.aclose)
        return LoggingStreamResponse(
            content=event_generator(r.aiter_raw()), logger=responselogger
        )
    else:
        r = await stream_client.send(req)
        responseData = r.json()
        tokens = responseData["usage"]["completion_tokens"]
        background_tasks.add_task(logger.log_usage_for_key, api_key, model, tokens)
        return responseData


@app.post("/v1/chat/completions")
async def infer(
    requestData: ChatCompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
):
    content = await request.body()
    req, model, stream = await build_request(
        requestData,
        request.headers.mutablecopy(),
        request.url.path,
        request.method,
        content.decode(),
    )
    if stream:
        responselogger = StreamLogger(
            logging_handler=logger, source=api_key, iskey=True, model=model
        )
        # no logging implemented yet...
        r = await stream_client.send(req, stream=True)
        background_tasks.add_task(r.aclose)
        return LoggingStreamResponse(
            content=event_generator(r.aiter_raw()), logger=responselogger
        )
    else:
        r = await stream_client.send(req)
        responseData = r.json()
        tokens = responseData["usage"]["completion_tokens"]
        background_tasks.add_task(logger.log_usage_for_key, api_key, model, tokens)
        return responseData


@app.post("/v1/embeddings")
async def infer(
    requestData: EmbeddingRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
):
    content = await request.body()
    req, model, stream = await build_request(
        requestData,
        request.headers.mutablecopy(),
        request.url.path,
        request.method,
        content.decode(),
    )
    r = await stream_client.send(req)
    responseData = r.json()
    tokens = responseData["usage"]["prompt_tokens"]
    background_tasks.add_task(logger.log_usage_for_key, api_key, model, tokens)
    return responseData


@app.get("/v1/models/")
@app.get("/v1/models")
def getModels():
    # At the moment hard-coded. Will update
    return {
        "object": "list",
        "data": [
            {
                "id": "llama2-7b-chat",
                "object": "model",
                "owned_by": "RSE",
                "permissions": [],
            },
            {
                "id": "llama2-7b",
                "object": "model",
                "owned_by": "RSE",
                "permissions": [],
            },
        ],
    }

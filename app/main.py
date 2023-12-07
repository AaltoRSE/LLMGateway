"""
A placeholder hello world app.
"""

from typing import Union
from fastapi import FastAPI, Request, BackgroundTasks, Security, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader

from utils.responses import LoggingStreamResponse, event_generator
from contextlib import asynccontextmanager
from functools import partial

from utils.requests import CompletionRequest, ChatCompletionRequest

from utils.stream_logger import StreamLogger
from utils.logging_handler import LoggingHandler
import httpx
import anyio

infernence_apikey = "123"
api_keys = ["321"]
availablemodels = {"llama2-7b": "llama2-7b", "llama2-7b-chat": "llama2-7b-chat"}
logger = LoggingHandler()
client = httpx.AsyncClient(base_url="https://llm.k8s-test.cs.aalto.fi")
api_key_header = APIKeyHeader(name="X-LLM-Key")


# Need to figure out how to offer two alternative authentication methods...
def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API Key",
    )


def parse_body(data: CompletionRequest | ChatCompletionRequest):
    # Extract data from request body
    # Replace this with your logic to extract data from the request body
    model = data.model
    stream = data.stream
    return model, stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    client = httpx.AsyncClient(base_url="https://llm.k8s-test.cs.aalto.fi")
    yield
    # Clean up the ML models and release the resources
    await client.aclose()


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


@app.post("/v1/chat/completions")
async def infer(
    requestData: ChatCompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
):
    model, stream = parse_body(requestData)
    url = httpx.URL(
        path=model + "/" + request.url.path, query=request.url.query.encode("utf-8")
    )
    headers = request.headers.mutablecopy()
    headers["X-APIkey"] = infernence_apikey
    req = client.build_request(
        request.method, url, headers=headers, content=await request.body()
    )
    if stream:
        responselogger = StreamLogger(
            logging_handler=logger, source=api_key, iskey=True, model=model
        )
        # no logging implemented yet...
        r = await client.send(req, stream=True)
        background_tasks.add_task(r.aclose())
        return LoggingStreamResponse(
            content=event_generator(r.aiter_raw()), logger=responselogger
        )
    else:
        response = await client.send(req)
        responseData = response.json()
        tokens = responseData["usage"]["total_tokens"]
        background_tasks.add_task(logger.log_usage_for_key(api_key, model, tokens))
        return responseData


@app.get("/v1/models/")
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

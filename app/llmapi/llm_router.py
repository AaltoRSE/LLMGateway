# LLM API Endpoints

from fastapi import (
    APIRouter,
    Request,
    BackgroundTasks,
    Security,
    HTTPException,
    FastAPI,
)

from .llama_requests import (
    ChatCompletionRequest,
)

from .llama_responses import (
    ModelList,
    ChatCompletion,
)

from utils.response_handling import LoggingStreamResponse, event_generator
from security.api_keys import get_api_key
from utils.handlers import (
    inference_request_builder,
    logging_handler,
)
from utils.stream_logger import StreamLogger
from contextlib import asynccontextmanager
from utils.quota import server_quota

import logging
import httpx
import os


llm_logger = logging.getLogger("app")


router = APIRouter(
    prefix="/v1",
    tags=["LLM Endpoints"],
)


stream_client = httpx.AsyncClient(base_url=os.environ.get("LLM_BASE_URL"))
llm_logger.info(stream_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    llm_logger.info("Lifespan called")
    stream_client = httpx.AsyncClient(base_url=os.environ.get("LLM_BASE_URL"))
    yield
    await stream_client.aclose()


@router.post("/chat/completions")
async def chat_completion(
    requestData: ChatCompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
) -> ChatCompletion:
    content = await request.body()
    stream = requestData.stream
    req = await inference_request_builder.build_request(
        requestData,
        request.headers.mutablecopy(),
        request.method,
        content.decode(),
        stream_client,
    )

    try:
        if stream:
            llm_logger.info("Trying to send streaming request to LLM")
            llm_logger.info(req.url)
            llm_logger.info(req.headers)
            llm_logger.info(req)
            responselogger = StreamLogger(
                logging_handler=logging_handler,
                source=api_key,
                iskey=True,
                model=server_quota.get_current_model(),
            )
            # no logging implemented yet...
            r = await stream_client.send(req, stream=True)
            if not r.status_code == httpx.codes.OK:
                raise HTTPException(r.status_code)
            background_tasks.add_task(r.aclose)
            return LoggingStreamResponse(
                content=event_generator(r.aiter_raw()),
                streamlogger=responselogger,
            )
        else:
            llm_logger.info("Trying to send non streaming request to LLM")
            llm_logger.info(req.url)
            llm_logger.info(req.headers)
            llm_logger.info(req)
            r = await stream_client.send(req)
            if not r.status_code == httpx.codes.OK:
                raise HTTPException(r.status_code)

            responseData = r.json()
            tokens = responseData["usage"]["completion_tokens"]
            background_tasks.add_task(
                logging_handler.log_usage_for_key,
                tokens,
                server_quota.get_current_model(),
                api_key,
            )
            background_tasks.add_task(server_quota.update_price, tokens, False)
            return responseData
    except HTTPException as e:
        llm_logger.exception(e)
        raise e
    except Exception as e:
        llm_logger.exception(e)
        # re-raise to let FastAPI handle it.
        raise HTTPException(status_code=500)


@router.get("/models/")
@router.get("/models")
def getModels() -> ModelList:
    # At the moment hard-coded. Will update
    model = server_quota.get_current_model()
    list = {
        "object": "list",
        "data": [
            {
                "id": model,
                "object": "model",
                "permissions": [],
                "created": 0,
                "owned_by": "Aalto University",
            }
        ],
    }
    return list

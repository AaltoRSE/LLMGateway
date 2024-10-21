# LLM API Endpoints

from fastapi import (
    APIRouter,
    Request,
    BackgroundTasks,
    Security,
    HTTPException,
    status,
    FastAPI,
    Depends,
)
from typing import Annotated
import logging
import httpx
import os

from llama_cpp.llama_types import (
    Completion,
    ChatCompletion,
    CreateEmbeddingResponse,
)
from llama_cpp.server.types import ModelList

# These are essentially the llama_cpp classes except, that they have a default value for the model
from app.requests.llama_requests import (
    CompletionRequest,
    ChatCompletionRequest,
    EmbeddingRequest,
)


from app.security.api_keys import get_api_key
from app.utils.request_building import BodyHandler
from app.utils.stream_response import LoggingStreamResponse, event_generator
from app.utils.stream_logger import StreamLogger
from app.models.keys import UserKey
from app.models.quota import RequestQuota
from app.services.model_service import ModelService
from app.services.quota_service import QuotaService
from contextlib import asynccontextmanager


llm_logger = logging.getLogger("app")


router = APIRouter(
    prefix="/v1",
    tags=["LLM Endpoints"],
)

llm_url = os.environ.get("LLM_DEFAULT_URL")

if os.environ.get("DEV_MODE", "0") == "1":
    stream_client = httpx.AsyncClient(base_url=llm_url, verify=False)
else:
    stream_client = httpx.AsyncClient(base_url=llm_url)
llm_logger.info(f"Request URL used is {llm_url}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    llm_logger.debug("Lifespan called")
    stream_client = httpx.AsyncClient(base_url=llm_url)
    yield
    await stream_client.aclose()


def requests_stream_usage(request: CompletionRequest | ChatCompletionRequest):
    """
    This function is used to log the usage of the stream.
    """
    if "stream_options" in request and "include_usage" in request.stream_options:
        return request.stream_options.include_usage
    return False


@router.post("/completions")
async def completion(
    requestData: CompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    quota_service: Annotated[QuotaService, Depends(QuotaService)],
    body_handler: Annotated[BodyHandler, Depends(BodyHandler)],
    api_key: UserKey = Security(get_api_key),
) -> Completion:
    # Check the quota, needs the api key before it can be done.
    quota_service.check_quota(api_key)
    stream = requestData.stream
    stream_usage = requests_stream_usage(requestData)
    req, model = await body_handler.build_request(
        requestData,
        request,
        stream_client,
        not stream_usage,  # if it has been true, we don't need to add it.
    )

    try:
        if stream:
            responselogger = StreamLogger(
                quota_service=quota_service, source=api_key, model=model
            )
            # no logging implemented yet...
            r = await stream_client.send(req, stream=True)
            background_tasks.add_task(r.aclose)
            return LoggingStreamResponse(
                content=event_generator(r.aiter_raw()),
                streamlogger=responselogger,
                include_usage=stream_usage,
            )
        else:
            llm_logger.info(req)
            r = await stream_client.send(req)
            llm_logger.debug(r.content)
            responseData = r.json()
            completion_tokens = responseData["usage"]["completion_tokens"]
            prompt_tokens = responseData["usage"]["prompt_tokens"]
            new_request = RequestQuota(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                prompt_cost=model.prompt_cost,
                completion_cost=model.completion_cost,
            )
            background_tasks.add_task(
                quota_service.update_quota, api_key, model.model.id, new_request
            )
            return responseData
    except HTTPException as e:
        llm_logger.exception(e)
        raise e
    except Exception as e:
        llm_logger.exception(e)
        # re-raise to let FastAPI handle it.
        raise HTTPException(status_code=500)


@router.post("/chat/completions")
async def chat_completion(
    requestData: ChatCompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    quota_service: Annotated[QuotaService, Depends(QuotaService)],
    body_handler: Annotated[BodyHandler, Depends(BodyHandler)],
    api_key: UserKey = Security(get_api_key),
) -> ChatCompletion:
    quota_service.check_quota(api_key)
    stream = requestData.stream
    stream_usage = requests_stream_usage(requestData)
    req, model = await body_handler.build_request(
        requestData,
        request,
        stream_client,
        stream and not stream_usage,  # if it has been true, we don't need to add it.
    )
    try:
        llm_logger.info(req)
        llm_logger.info(req.content)
        if stream:
            responselogger = StreamLogger(
                quota_service=quota_service, source=api_key, model=model
            )
            # no logging implemented yet...
            r = await stream_client.send(req, stream=True)
            background_tasks.add_task(r.aclose)
            return LoggingStreamResponse(
                content=event_generator(r.aiter_raw()),
                streamlogger=responselogger,
                include_usage=stream_usage,
            )
        else:
            r = await stream_client.send(req)
            llm_logger.info(r.content)
            responseData = r.json()
            completion_tokens = responseData["usage"]["completion_tokens"]
            prompt_tokens = responseData["usage"]["prompt_tokens"]
            new_request = RequestQuota(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                prompt_cost=model.prompt_cost,
                completion_cost=model.completion_cost,
            )
            background_tasks.add_task(
                quota_service.update_quota, api_key, model.model.id, new_request
            )
            return responseData
    except HTTPException as e:
        llm_logger.exception(e)
        raise e
    except Exception as e:
        llm_logger.exception(e)
        # re-raise to let FastAPI handle it.
        raise HTTPException(status_code=500)


@router.post("/embeddings")
async def embedding(
    requestData: EmbeddingRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    quota_service: Annotated[QuotaService, Depends(QuotaService)],
    body_handler: Annotated[BodyHandler, Depends(BodyHandler)],
    api_key: UserKey = Security(get_api_key),
) -> CreateEmbeddingResponse:
    quota_service.check_quota(api_key)
    req, model = await body_handler.build_request(
        requestData,
        request,
        stream_client,
        False,  # In here, we don't even have the field to add it.
    )
    try:
        llm_logger.debug(req.content)
        r = await stream_client.send(req)
        responseData = r.json()
        completion_tokens = responseData["usage"]["completion_tokens"]
        prompt_tokens = responseData["usage"]["prompt_tokens"]
        new_request = RequestQuota(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_cost=model.prompt_cost,
            completion_cost=model.completion_cost,
        )
        background_tasks.add_task(
            quota_service.update_quota, api_key, model.model.id, new_request
        )
        return responseData
    except HTTPException as e:
        llm_logger.exception(e)
        raise e
    except Exception as e:
        llm_logger.exception(e)
        raise HTTPException(status_code=500)


@router.get("/models/")
@router.get("/models")
def getModels(
    model_handler: Annotated[ModelService, Depends(ModelService)],
) -> ModelList:
    # At the moment hard-coded. Will update
    models = model_handler.get_api_models()
    model_list = [model.model_dump() for model in models]
    llm_logger.info(model_list)
    if len(models) > 0:
        return {
            "object": "list",
            "data": [model.model_dump() for model in models],
        }
    else:
        # Should never actually happen, since it should always have one...
        raise HTTPException(status.HTTP_418_IM_A_TEAPOT)


@router.post("/test_key")
@router.get("/test_key")
def test_key(api_key: UserKey = Security(get_api_key)):
    return {"api_key"}

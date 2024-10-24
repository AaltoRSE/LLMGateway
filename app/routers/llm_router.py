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
from typing import Annotated, Union
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
from app.utils.stream_response import LoggingStreamResponse, event_generator
from app.utils.stream_logger import StreamLogger
from app.models.keys import UserKey
from app.models.quota import RequestQuota
from app.services.model_service import ModelService
from app.services.quota_service import QuotaService
from app.services.request_service import RequestService
from contextlib import asynccontextmanager


llm_logger = logging.getLogger("app")


router = APIRouter(
    prefix="/v1",
    tags=["LLM Endpoints"],
)

stream_client: httpx.AsyncClient | None = httpx.AsyncClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    llm_logger.info("Creating stream client")
    stream_client = httpx.AsyncClient()
    yield
    llm_logger.info("Closing stream client")
    # Close the client
    await stream_client.aclose()
    # reset the client
    stream_client = None


@router.post("/completions")
async def completion(
    requestData: CompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    quota_service: Annotated[QuotaService, Depends(QuotaService)],
    request_handler: Annotated[RequestService, Depends(RequestService)],
    api_key: UserKey = Security(get_api_key),
) -> Completion:
    # Check the quota, needs the api key before it can be done.
    quota_service.check_quota(api_key)
    llm_request = await request_handler.generate_client_and_request(
        requestData, request, stream_client
    )

    try:
        if llm_request.streaming:
            responselogger = StreamLogger(
                quota_service=quota_service, source=api_key, model=llm_request.model
            )
            # no logging implemented yet...
            r = await stream_client.send(llm_request.request, stream=True)
            if r.status_code >= 400:
                raise HTTPException(status_code=r.status_code, detail=r.content)
            background_tasks.add_task(r.aclose)
            return LoggingStreamResponse(
                content=event_generator(r.aiter_raw()),
                streamlogger=responselogger,
                include_usage=llm_request.stream_usage_requested,
            )
        else:
            llm_logger.info(llm_request.request)
            r = await stream_client.send(llm_request.request)
            llm_logger.debug(r.content)
            if r.status_code >= 400:
                raise HTTPException(status_code=r.status_code, detail=r.content)
            responseData = r.json()
            completion_tokens = responseData["usage"]["completion_tokens"]
            prompt_tokens = responseData["usage"]["prompt_tokens"]
            new_request = RequestQuota(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                prompt_cost=llm_request.model.prompt_cost,
                completion_cost=llm_request.model.completion_cost,
            )
            background_tasks.add_task(
                quota_service.update_quota,
                api_key,
                llm_request.model.model.id,
                new_request,
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
    request_handler: Annotated[RequestService, Depends(RequestService)],
    api_key: UserKey = Security(get_api_key),
) -> ChatCompletion:
    quota_service.check_quota(api_key)
    llm_request = await request_handler.generate_client_and_request(
        requestData, request, stream_client
    )

    try:
        llm_logger.info(llm_request)
        if llm_request.streaming:
            responselogger = StreamLogger(
                quota_service=quota_service, source=api_key, model=llm_request.model
            )
            # no logging implemented yet...
            r = await stream_client.send(llm_request.request, stream=True)
            llm_logger.info(r.status_code)
            if r.status_code >= 400:
                raise HTTPException(status_code=r.status_code, detail=r.content)
            background_tasks.add_task(r.aclose)
            llm_logger.info(r)
            return LoggingStreamResponse(
                content=event_generator(r.aiter_raw()),
                streamlogger=responselogger,
                include_usage=llm_request.stream_usage_requested,
            )
        else:
            r = await stream_client.send(llm_request.request)
            llm_logger.info(r.content)
            if r.status_code >= 400:
                raise HTTPException(status_code=r.status_code, detail=r.content)
            responseData = r.json()
            completion_tokens = responseData["usage"]["completion_tokens"]
            prompt_tokens = responseData["usage"]["prompt_tokens"]
            new_request = RequestQuota(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                prompt_cost=llm_request.model.prompt_cost,
                completion_cost=llm_request.model.completion_cost,
            )
            background_tasks.add_task(
                quota_service.update_quota,
                api_key,
                llm_request.model.model.id,
                new_request,
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
    request_handler: Annotated[RequestService, Depends(RequestService)],
    api_key: UserKey = Security(get_api_key),
) -> CreateEmbeddingResponse:
    quota_service.check_quota(api_key)
    llm_request = await request_handler.generate_client_and_request(
        requestData, request, stream_client
    )
    try:
        llm_logger.debug(llm_request.request.content)
        r = await stream_client.send(llm_request.request)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.content)
        responseData = r.json()
        completion_tokens = responseData["usage"]["completion_tokens"]
        prompt_tokens = responseData["usage"]["prompt_tokens"]
        new_request = RequestQuota(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_cost=llm_request.model.prompt_cost,
            completion_cost=llm_request.model.completion_cost,
        )
        background_tasks.add_task(
            quota_service.update_quota, api_key, llm_request.model.model.id, new_request
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

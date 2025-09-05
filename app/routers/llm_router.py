# LLM API Endpoints

from fastapi import (
    APIRouter,
    Security,
    HTTPException,
    Depends,
)
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from typing import Annotated, Callable
import logging

# These are essentially the llama_cpp classes except, that they have a default value for the model


from typing import Annotated, Any
from openai.types.create_embedding_response import CreateEmbeddingResponse
from fastapi import APIRouter, Depends, HTTPException, Security
from app.schemas.openai_schemas import (
    ChatCompletionStreamOptions,
    CreateResponse,
    CreateEmbeddingRequest,
)
from app.schemas.usage_schema import APIRequest
from app.security.auth import get_user, BackendUser

from app.services.usage_service import UsageService
from app.services.model_service import ModelService

llm_logger = logging.getLogger("app")

router = APIRouter(
    prefix="/api/v1",
    tags=["LLM Endpoints"],
)

# FIXME: This should probably either be an environment variable or
# some other configuration element.
default_model = "gpt-4o"


@router.post("/responses", response_model=None)
async def create_response(
    request_data: CreateResponse,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    model_service: Annotated[ModelService, Depends(ModelService)],
    current_user: BackendUser = Security(get_user),
) -> (
    JSONResponse | EventSourceResponse
):  # We will not define this further, as it otherwise will get painful, if the API changes.
    if usage_service.get_current_balance(current_user).used_up():
        raise HTTPException(402, "User out of Quota")
    try:
        model = model_service.get_llm_model(
            request_data.model if not request_data.model is None else default_model
        )
    except ValueError:
        raise HTTPException(404, "The requested model is not available on the server")
    usage_callback: Callable[[APIRequest], Any] = lambda usage: usage_service.log_usage(
        user=current_user, usage=usage
    )
    if request_data.stream:
        stream_iterator = await model.stream_response_request(
            user=current_user,
            request=request_data,
            usage_callback=usage_callback,
        )
        return EventSourceResponse(content=stream_iterator)
    else:
        response_data = await model.non_stream_response_request(
            user=current_user, request=request_data, usage_callback=usage_callback
        )
        return JSONResponse(content=response_data.model_dump())


@router.post("/chat/completions", response_model=None)
async def chat_completion(
    request_data: ChatCompletionRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    model_service: Annotated[ModelService, Depends(ModelService)],
    current_user: BackendUser = Security(get_user),
) -> (
    JSONResponse | EventSourceResponse
):  # We will not define this further, as it otherwise will get painful, if the API changes.
    if usage_service.get_current_balance(current_user).used_up():
        raise HTTPException(402, "User out of Quota")
    try:
        model = model_service.get_llm_model(
            request_data.model if not request_data.model is None else default_model
        )
    except ValueError:
        raise HTTPException(404, "The requested model is not available on the server")
    usage_callback: Callable[[APIRequest], Any] = lambda usage: usage_service.log_usage(
        user=current_user, usage=usage
    )
    if request_data.stream:
        added_usage = False
        if request_data.stream_options is None:
            request_data.stream_options = ChatCompletionStreamOptions(
                include_usage=True
            )
            added_usage = True
        else:
            if not request_data.stream_options.include_usage:
                request_data.stream_options.include_usage = True
                added_usage = True
        stream_iterator = await model.stream_chat_request(
            user=current_user,
            request=request_data,
            usage_callback=usage_callback,
            filter_usage=added_usage,
        )
        return EventSourceResponse(content=stream_iterator)
    else:
        response_data = await model.non_stream_chat_request(
            user=current_user, request=request_data, usage_callback=usage_callback
        )
        return JSONResponse(content=response_data.model_dump())


@router.post("/embeddings")
async def embedding(
    request_data: EmbeddingRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    model_service: Annotated[ModelService, Depends(ModelService)],
    current_user: BackendUser = Security(get_user),
) -> CreateEmbeddingResponse:

    if usage_service.get_current_balance(current_user).used_up():
        raise HTTPException(402, "User out of Quota")
    try:
        model = model_service.get_embedding_model(request_data.model)
    except ValueError:
        raise HTTPException(404, "The requested model is not available on the server")
    usage_callback: Callable[[APIRequest], Any] = lambda usage: usage_service.log_usage(
        user=current_user, usage=usage
    )
    return model.embed(
        user=current_user, request=request_data, usage_callback=usage_callback
    )

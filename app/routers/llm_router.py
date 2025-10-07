"""
LLM Endpoints
"""

import logging
from typing import Annotated, Any, List, Callable

from fastapi import APIRouter, Depends, HTTPException, Security, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.schemas.openai_schemas import (
    CreateResponse,
    CreateEmbeddingRequest,
    CreateChatCompletionRequest,
    CreateEmbeddingResponse,
)

from app.security.authentication_dependencies import requires_auth, BackendUser

from app.services.usage_service import UsageService, Quota, APIRequest
from app.services.model_service import ModelService, LLMModelDataDetails
from app.config import app_configuration

llm_logger = logging.getLogger("app")

router = APIRouter(prefix="/api/v1", tags=["LLM Endpoints"])


async def out_of_quota(
    usage_service: Annotated[UsageService, Depends(UsageService)],
    current_user: BackendUser = Depends(requires_auth),
) -> bool:
    """
    Function that checks, whether the user is out of quota.
    """
    balance: Quota = await usage_service.get_quota_for_request(
        current_user.request_source
    )
    return balance.used_up()


@router.get("/models")
async def get_models(
    model_service: Annotated[ModelService, Depends(ModelService)],
) -> List[LLMModelDataDetails]:
    """
    Get the (API spec) of the models available on the gateway
    """
    models = await model_service.get_api_models()
    return models


@router.post("/responses", response_model=None)
async def create_response(
    request: Request,
    request_data: CreateResponse,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    model_service: Annotated[ModelService, Depends(ModelService)],
    current_user: BackendUser = Security(requires_auth),
    quota_exceeded: bool = Depends(out_of_quota),
) -> (
    JSONResponse | EventSourceResponse
):  # We will not define this further, as it otherwise will get painful, if the API changes.
    """
    Responses API
    """
    if quota_exceeded:
        raise HTTPException(402, "User out of Quota")
    try:
        model = await model_service.get_model(
            request_data.model
            if not request_data.model is None
            else app_configuration.default_chat_model
        )
    except ValueError as exc:
        raise HTTPException(
            404, "The requested model is not available on the server"
        ) from exc
    model.check_type("responses")

    async def usage_callback(usage: APIRequest) -> None:
        await usage_service.log_usage(source=current_user.request_source, usage=usage)

    if request_data.stream:

        return EventSourceResponse(
            content=model.stream_response_request(
                request=request,
                usage_callback=usage_callback,
            )
        )

    response_data = await model.non_stream_response_request(
        request=request, usage_callback=usage_callback
    )
    return JSONResponse(content=response_data.model_dump())


@router.post("/chat/completions", response_model=None)
async def chat_completion(
    request_data: CreateChatCompletionRequest,
    request: Request,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    model_service: Annotated[ModelService, Depends(ModelService)],
    current_user: BackendUser = Security(requires_auth),
    quota_exceeded: bool = Depends(out_of_quota),
) -> (
    JSONResponse | EventSourceResponse
):  # We will not define this further, as it otherwise will get painful, if the API changes.
    """
    Completions API
    """
    if quota_exceeded:
        raise HTTPException(402, "User out of Quota")
    try:
        model = await model_service.get_model(
            request_data.model
            if not request_data.model is None
            else app_configuration.default_chat_model
        )

    except ValueError as exc:
        raise HTTPException(
            404, "The requested model is not available on the server"
        ) from exc
    model.check_type("chat")

    async def usage_callback(usage: APIRequest) -> None:
        await usage_service.log_usage(source=current_user.request_source, usage=usage)

    if request_data.stream:
        add_usage = False
        if request_data.stream_options is None:
            add_usage = True
        else:
            if not request_data.stream_options.include_usage:
                add_usage = True
        llm_logger.debug("Add Stream usage? %s", add_usage)
        return EventSourceResponse(
            content=model.stream_chat_request(
                request=request,
                usage_callback=usage_callback,
                filter_usage=add_usage,
            )
        )

    response_data = await model.non_stream_chat_request(
        request=request, usage_callback=usage_callback
    )
    return JSONResponse(content=response_data.model_dump())


@router.post("/embeddings")
async def embedding(
    request: Request,
    request_data: CreateEmbeddingRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    model_service: Annotated[ModelService, Depends(ModelService)],
    current_user: BackendUser = Security(requires_auth),
    quota_exceeded: bool = Depends(out_of_quota),
) -> CreateEmbeddingResponse:
    """
    Embedding API
    """
    if quota_exceeded:
        raise HTTPException(402, "User out of Quota")
    try:
        model = await model_service.get_model(
            request_data.model
            if request_data.model is not None
            else app_configuration.default_embedding_model
        )
    except ValueError as exc:
        raise HTTPException(
            404, "The requested model is not available on the server"
        ) from exc
    model.check_type("embedding")

    usage_callback: Callable[[APIRequest], Any] = lambda usage: usage_service.log_usage(
        source=current_user.request_source, usage=usage
    )

    return await model.embed(request=request, usage_callback=usage_callback)

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


from typing import Annotated, Any, List
from fastapi import APIRouter, Depends, HTTPException, Security
from app.schemas.openai_schemas import (
    ChatCompletionStreamOptions,
    CreateResponse,
    CreateEmbeddingRequest,
    CreateChatCompletionRequest,
    CreateEmbeddingResponse,
)
from app.schemas.usage_schema import APIRequest, Balance
from app.schemas.llmmodel_schema import LLMModelDataDetails
from app.security.authentication_dependencies import requires_auth, BackendUser

from app.services.usage_service import UsageService
from app.services.model_service import ModelService
from app.config import app_configuration

llm_logger = logging.getLogger("app")

router = APIRouter(
    prefix="/api/v1",
    tags=["LLM Endpoints"],
)

# FIXME: This should probably either be an environment variable or
# some other configuration element.
default_model = "gpt-4o"


async def out_of_quota(
    usage_service: Annotated[UsageService, Depends(UsageService)],
    current_user: BackendUser = Depends(requires_auth),
) -> bool:
    balance: Balance = await usage_service.get_balance_for_request(
        current_user.request_source
    )
    return balance.used_up()


@router.get("/models")
async def get_models(
    model_service: Annotated[ModelService, Depends(ModelService)],
) -> List[LLMModelDataDetails]:
    models = await model_service.get_api_models()
    return models


@router.post("/responses", response_model=None)
async def create_response(
    request_data: CreateResponse,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    model_service: Annotated[ModelService, Depends(ModelService)],
    current_user: BackendUser = Security(requires_auth),
    out_of_quota: bool = Depends(out_of_quota),
) -> (
    JSONResponse | EventSourceResponse
):  # We will not define this further, as it otherwise will get painful, if the API changes.

    if out_of_quota:
        raise HTTPException(402, "User out of Quota")
    try:
        model = await model_service.get_model(
            request_data.model
            if not request_data.model is None
            else app_configuration.default_chat_model
        )
    except ValueError:
        raise HTTPException(404, "The requested model is not available on the server")
    usage_callback: Callable[[APIRequest], Any] = lambda usage: usage_service.log_usage(
        source=current_user.request_source, usage=usage
    )
    if request_data.stream:
        stream_iterator = await model.stream_response_request(
            request=request_data,
            usage_callback=usage_callback,
        )
        return EventSourceResponse(content=stream_iterator)
    else:
        response_data = await model.non_stream_response_request(
            request=request_data, usage_callback=usage_callback
        )
        return JSONResponse(content=response_data.model_dump())


@router.post("/chat/completions", response_model=None)
async def chat_completion(
    request_data: CreateChatCompletionRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    model_service: Annotated[ModelService, Depends(ModelService)],
    current_user: BackendUser = Security(requires_auth),
    out_of_quota: bool = Depends(out_of_quota),
) -> (
    JSONResponse | EventSourceResponse
):  # We will not define this further, as it otherwise will get painful, if the API changes.
    if out_of_quota:
        raise HTTPException(402, "User out of Quota")
    try:
        model = await model_service.get_model(
            request_data.model
            if not request_data.model is None
            else app_configuration.default_chat_model
        )

    except ValueError:
        raise HTTPException(404, "The requested model is not available on the server")

    async def usage_callback(usage: APIRequest) -> None:
        await usage_service.log_usage(source=current_user.request_source, usage=usage)

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
            request=request_data,
            usage_callback=usage_callback,
            filter_usage=added_usage,
        )
        return EventSourceResponse(content=stream_iterator)
    else:
        response_data = await model.non_stream_chat_request(
            request=request_data, usage_callback=usage_callback
        )
        return JSONResponse(content=response_data.model_dump())


@router.post("/embeddings")
async def embedding(
    request_data: CreateEmbeddingRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    model_service: Annotated[ModelService, Depends(ModelService)],
    current_user: BackendUser = Security(requires_auth),
    out_of_quota: bool = Depends(out_of_quota),
) -> CreateEmbeddingResponse:

    if out_of_quota:
        raise HTTPException(402, "User out of Quota")
    try:
        model = await model_service.get_model(
            request_data.model
            if request_data.model is not None
            else app_configuration.default_embedding_model
        )
    except ValueError:
        raise HTTPException(404, "The requested model is not available on the server")
    usage_callback: Callable[[APIRequest], Any] = lambda usage: usage_service.log_usage(
        source=current_user.request_source, usage=usage
    )
    return await model.embed(request=request_data, usage_callback=usage_callback)

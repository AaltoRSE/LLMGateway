# LLM API Endpoints

from fastapi import (
    APIRouter,
    Request,
    BackgroundTasks,
    Security,
    HTTPException,
    status,
    FastAPI,
)

from fastapi.responses import (
    StreamingResponse,    
)

# These are essentially the llama_cpp classes except, that they have a default value for the model
from .llama_requests import (
    CompletionRequest,
    ChatCompletionRequest,
    EmbeddingRequest,
)

from llama_cpp.llama_types import (
    Completion,
    ChatCompletion,
    CreateEmbeddingResponse,
)
from llama_cpp.server.types import ModelList

from security.api_keys import get_api_key
from utils.handlers import (
    model_handler,
    inference_request_builder,
    logging_handler,
)
from server_logging.stream_logger import StreamLogger
from contextlib import asynccontextmanager


import logging
import httpx
import os


llm_logger = logging.getLogger("app")


router = APIRouter(
    prefix="/v1",
    tags=["LLM Endpoints"],
)

llm_logger.info(f"Request URL used is {os.environ.get("LLM_BASE_URL")}")
stream_client = httpx.AsyncClient(base_url=os.environ.get("LLM_BASE_URL"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    llm_logger.debug("Lifespan called")
    stream_client = httpx.AsyncClient(base_url=os.environ.get("LLM_BASE_URL"))
    yield
    await stream_client.aclose()


@router.post("/completions")
async def completion(
    requestData: CompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
) -> Completion:
    content = await request.body()
    llm_logger.debug(content)
    stream = requestData.stream
    llm_logger.debug(stream_client)
    req, model = await inference_request_builder.build_request(
        requestData,
        request.headers.mutablecopy(),
        request.url.path,
        request.method,
        content.decode(),
        stream_client,
    )
    try:
        if stream:            
            # TODO: Conditionally add "stream_options.include_usage" to the request (and delete the respective cunk from the response)
            # no logging implemented yet...            
            r = await stream_client.send(req, stream=True)
            responselogger = StreamLogger(

                logging_handler=logging_handler, source=api_key, iskey=True, model=requestData.model, stream = r.aiter_text()
            )
            background_tasks.add_task(r.aclose)
            background_tasks.add_task(responselogger.finish)
            return StreamingResponse(responselogger.process())
        
        else:
            r = await stream_client.send(req)
            llm_logger.debug(r.content)
            responseData = r.json()
            tokens = responseData["usage"]["completion_tokens"]
            background_tasks.add_task(
                logging_handler.log_usage_for_key, tokens, requestData.model, api_key
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
    api_key: str = Security(get_api_key),
) -> ChatCompletion:
    content = await request.body()
    llm_logger.debug(content)
    stream = requestData.stream    
    req, modelpath = await inference_request_builder.build_request(
        requestData,
        request.headers.mutablecopy(),
        request.url.path,
        request.method,
        content.decode(),
        stream_client,
    )
    llm_logger.info(req)
    try:
        if stream:
            r = await stream_client.send(req, stream=True)
            responselogger = StreamLogger(
                logging_handler=logging_handler, source=api_key, iskey=True, model=requestData.model, stream = r.aiter_text()
            )
            background_tasks.add_task(r.aclose)
            background_tasks.add_task(responselogger.finish)
            return StreamingResponse(responselogger.process())
        else:            
            r = await stream_client.send(req)
            llm_logger.debug(r.content)
            responseData = r.json()
            tokens = responseData["usage"]["completion_tokens"]
            background_tasks.add_task(
                logging_handler.log_usage_for_key, tokens, requestData.model, api_key
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
    api_key: str = Security(get_api_key),
) -> CreateEmbeddingResponse:
    content = await request.body()
    llm_logger.debug(content)
    req = await inference_request_builder.build_request(
        requestData,
        request.headers.mutablecopy(),
        request.url.path,
        request.method,
        content.decode(),
        stream_client,
    )
    try:
        llm_logger.debug(req.content)
        r = await stream_client.send(req)
        responseData = r.json()
        tokens = responseData["usage"]["prompt_tokens"]
        background_tasks.add_task(
            logging_handler.log_usage_for_key, tokens, requestData.model, api_key
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
def getModels() -> ModelList:
    # At the moment hard-coded. Will update
    models = model_handler.get_models()
    if len(models) > 0:
        return {
            "object": "list",
            "data": models,
        }
    else:
        # Should never actually happen, since it should always have one...
        raise HTTPException(status.HTTP_418_IM_A_TEAPOT)

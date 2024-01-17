"""
A placeholder hello world app.
"""

from typing import Union
from functools import partial

from fastapi import Depends, FastAPI, Request, BackgroundTasks, Security, HTTPException, Response
from fastapi.security import APIKeyHeader
from fastapi import status

from onelogin.saml2.auth import OneLogin_Saml2_Auth

import httpx
import logging
import re

from starlette.datastructures import MutableHeaders
from starlette.responses import RedirectResponse

from contextlib import asynccontextmanager

from utils.llama_requests import (
    CompletionRequest,
    ChatCompletionRequest,
    EmbeddingRequest,
)
from utils.llama_responses import ModelList, Completion, ChatCompletion, Embedding
from utils.api_requests import (
    AddAvailableModelRequest,
    RemoveModelRequest,
    AddApiKeyRequest,
)

from utils.saml_setup import saml_settings

from utils.api_responses import LoggingStreamResponse, event_generator
from utils.stream_logger import StreamLogger
from utils.logging_handler import LoggingHandler
from utils.key_handler import KeyHandler
from utils.model_handler import ModelHandler
from utils.serverlogging import RouterLogging
from utils.request_building import BodyHandler
from security.api_keys import get_api_key, get_admin_key, key_handler

import os


model_handler = ModelHandler()
logger = LoggingHandler()
logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
uvlogger = logging.getLogger("app")
key_handler.set_logger(uvlogger)

inference_request_builder = BodyHandler(uvlogger, model_handler)

inference_apikey = "Bearer " + os.environ.get("INFERENCE_KEY")
stream_client = httpx.AsyncClient(base_url="https://llm.k8s-test.cs.aalto.fi")
api_key_header = APIKeyHeader(name="Authorization")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    stream_client = httpx.AsyncClient(base_url="https://llm.k8s-test.cs.aalto.fi")
    yield
    # Clean up the ML models and release the resources
    await stream_client.aclose()


app = FastAPI(lifespan=lifespan, debug=True)
# Add Request logging
app.add_middleware(RouterLogging, logger=uvlogger)


@app.post("/v1/completions")
async def completion(
    requestData: CompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
) -> Completion:
    content = await request.body()
    uvlogger.info(content)
    req, model, stream = await inference_request_builder.build_request(
        requestData,
        request.headers.mutablecopy(),
        request.url.path,
        request.method,
        content.decode(),
        stream_client,
    )
    try:
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
    except Exception as e:
        uvlogger.exception(e)
        # re-raise to let FastAPI handle it.
        raise e


@app.post("/v1/chat/completions")
async def chat_completion(
    requestData: ChatCompletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
) -> ChatCompletion:
    content = await request.body()
    uvlogger.info(content)
    req, model, stream = await inference_request_builder.build_request(
        requestData,
        request.headers.mutablecopy(),
        request.url.path,
        request.method,
        content.decode(),
        stream_client,
    )
    try:
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
    except Exception as e:
        uvlogger.exception(e)
        # re-raise to let FastAPI handle it.
        raise e


@app.post("/v1/embeddings")
async def embedding(
    requestData: EmbeddingRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
) -> Embedding:
    content = await request.body()
    uvlogger.info(content)
    req, model, stream = await inference_request_builder.build_request(
        requestData,
        request.headers.mutablecopy(),
        request.url.path,
        request.method,
        content.decode(),
        stream_client,
    )
    try:
        r = await stream_client.send(req)
        responseData = r.json()
        tokens = responseData["usage"]["prompt_tokens"]
        background_tasks.add_task(logger.log_usage_for_key, api_key, model, tokens)
        return responseData
    except Exception as e:
        uvlogger.exception(e)
        raise e


@app.get("/v1/models/")
@app.get("/v1/models")
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


@app.post("/admin/addmodel", status_code=status.HTTP_201_CREATED)
def addModel(
    RequestData: AddAvailableModelRequest, admin_key: str = Security(get_admin_key)
):
    try:
        model_handler.add_model(RequestData)
    except KeyError as e:
        raise HTTPException(status.HTTP_409_CONFLICT)


@app.post("/admin/removemodel", status_code=status.HTTP_200_OK)
def removemodel(
    RequestData: RemoveModelRequest, admin_key: str = Security(get_admin_key)
):
    try:
        model_handler.remove_model(RequestData)
    except KeyError as e:
        raise HTTPException(status.HTTP_410_GONE)


@app.post("/admin/addapikey", status_code=status.HTTP_201_CREATED)
def addKey(RequestData: AddApiKeyRequest, admin_key: str = Security(get_admin_key)):
    if key_handler.add_key(
        user=RequestData.user, api_key=RequestData.key, name=RequestData.name
    ):
        pass
    else:
        raise HTTPException(409, "Key already exists")


@app.post("/admin/removeapikey", status_code=status.HTTP_200_OK)
def removeKey(RequestData: AddApiKeyRequest, admin_key: str = Security(get_admin_key)):
    if key_handler.delete_key(key=RequestData.key):
        pass
    else:
        raise HTTPException(409, "Key already exists")

@app.get("/admin/listkeys", status_code=status.HTTP_200_OK)
def listKeys(RequestData: Request, admin_key: str = Security(get_admin_key)):
    uvlogger.info("Keys requested")
    return key_handler.list_keys()

async def prepare_from_fastapi_request(request: Request, debug=False):
    uvlogger.info(request.client.host)
    uvlogger.info(request.url.port)
    uvlogger.info(request.url.path)
    uvlogger.info(request.headers.get("X-Forwarded-For"))
    uvlogger.info(request.client)
    uvlogger.info(request.url)
    rv = {
        "http_host": request.url.hostname,
        "server_port": request.url.port,
        "script_name": request.url.path,
        "post_data": {},
        "get_data": {},
        # Advanced request options
        "https": ""
        # "request_uri": "",
        # "query_string": "",
        # "validate_signature_from_qs": False,
        # "lowercase_urlencoding": False
    }
    if request.query_params:
        rv["get_data"] = (request.query_params,)
    form_data = await request.form()
    uvlogger.info(form_data)
    if "SAMLResponse" in form_data:
        SAMLResponse = form_data["SAMLResponse"]
        rv["post_data"]["SAMLResponse"] = SAMLResponse
    if "RelayState" in form_data:
        RelayState = form_data["RelayState"]
        rv["post_data"]["RelayState"] = RelayState

    return rv


@app.get("/saml/login")
async def login(request: Request):
    req = await prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, saml_settings)
    # saml_settings = auth.get_settings()
    # metadata = saml_settings.get_sp_metadata()
    # errors = saml_settings.validate_metadata(metadata)
    # if len(errors) == 0:
    #   print(metadata)
    # else:
    #   print("Error found on Metadata: %s" % (', '.join(errors)))
    callback_url = auth.login()
    response = RedirectResponse(url=callback_url)
    return response


@app.post("/saml/acs")
async def saml_callback(request: Request):
    req = await prepare_from_fastapi_request(request, True)
    uvlogger.info(saml_settings.get_idp_data())
    auth = OneLogin_Saml2_Auth(req, saml_settings)
    auth.process_response()  # Process IdP response
    errors = auth.get_errors()  # This method receives an array with the errors
    if len(errors) == 0:
        if (
            not auth.is_authenticated()
        ):  # This check if the response was ok and the user data retrieved or not (user authenticated)
            return "user Not authenticated"
        else:
            uvlogger.info(auth.get_attributes())
            return "User authenticated"
    else:
        print(
            "Error when processing SAML Response: %s %s"
            % (", ".join(errors), auth.get_last_error_reason())
        )
        return "Error in callback"


@app.get("/saml/metadata")
async def metadata():
    metadata = saml_settings.get_sp_metadata()
    return Response(content=metadata, media_type="text/xml")

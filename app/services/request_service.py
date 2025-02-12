from starlette.datastructures import MutableHeaders
from fastapi import HTTPException, status, Depends, Request
from typing import Annotated, Tuple
from pydantic import BaseModel, ConfigDict
import httpx
import json
import logging
import os

from app.requests.protocol import (
    CompletionRequest,
    ChatCompletionRequest,
    EmbeddingRequest,
)
from app.services.model_service import ModelService
from app.models.model import LLMModel

logger = logging.getLogger("app")


class LLMRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    model: LLMModel
    request: httpx.Request
    streaming: bool
    stream_usage_requested: bool = True


def requests_stream_usage(request: CompletionRequest | ChatCompletionRequest):
    """
    This function is used to log the usage of the stream.
    """
    if "stream_options" in request and "include_usage" in request.stream_options:
        return request.stream_options.include_usage
    return False


class RequestService:
    def __init__(self, model_handler: Annotated[ModelService, Depends(ModelService)]):
        self.model_handler = model_handler
        self.inference_apikey = "Bearer " + os.environ.get("INFERENCE_KEY")

    async def generate_client_and_request(
        self,
        requestData: ChatCompletionRequest | CompletionRequest | EmbeddingRequest,
        request: Request,
        stream_client=httpx.AsyncClient,
    ) -> LLMRequest:
        # Add the API Key for the inference server
        headers = request.headers.mutablecopy()
        headers["Authorization"] = self.inference_apikey
        # Get the model
        try:
            model = self.model_handler.get_model(requestData.model)
        except KeyError as e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Requested Model not available"
            )
        # set the request path and host
        path = request.url.path
        url = httpx.URL(model.path + path)
        stream_usage_requested = True
        streaming = False
        if not request is EmbeddingRequest:
            stream_usage_requested = requests_stream_usage(requestData)
            streaming = requestData.stream
        # Extract the body for forwarding
        content = await request.body()
        body = content.decode()
        # And update if necessary
        if streaming and not stream_usage_requested:
            body_dict = json.loads(body)
            if not "stream_options" in body_dict:
                body_dict["stream_options"] = {}
            if not "include_usage" in body_dict["stream_options"]:
                body_dict["stream_options"]["include_usage"] = True
            body = json.dumps(body_dict)
            headers["Content-Length"] = str(len(body.encode("utf-8")))
        # get the method
        method = request.method
        req = stream_client.build_request(
            method,
            url,
            headers=headers,
            content=body,
            timeout=600.0,
        )

        return LLMRequest(
            model=model,
            request=req,
            streaming=streaming,
            stream_usage_requested=stream_usage_requested,
        )

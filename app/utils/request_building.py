from starlette.datastructures import MutableHeaders
from fastapi import HTTPException, status, Depends, Request
from typing import Annotated, Tuple
import httpx
import json
import logging
import os


from app.requests.llama_requests import (
    CompletionRequest,
    ChatCompletionRequest,
    EmbeddingRequest,
)
from app.services.model_service import ModelService
from app.models.model import LLMModel

llm_url = "llm.k8s-test.cs.aalto.fi"
if "LLM_DEFAULT_URL" in os.environ:
    llm_url = os.environ.get("LLM_DEFAULT_URL")
    if llm_url.startswith("http"):
        # remove protocol
        llm_url = llm_url.split("://", maxsplit=1)[1]

logger = logging.getLogger("app")


class BodyHandler:
    def __init__(self, model_handler: Annotated[ModelService, Depends(ModelService)]):
        self.model_handler = model_handler
        self.inference_apikey = "Bearer " + os.environ.get("INFERENCE_KEY")

    def parse_body(
        self,
        data: CompletionRequest | ChatCompletionRequest | EmbeddingRequest,
    ) -> LLMModel:
        # Extract data from request body
        # Replace this with your logic to extract data from the request body
        try:
            model = self.model_handler.get_model(data.model)
        except KeyError as e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Requested Model not available"
            )

        return model

    async def build_request(
        self,
        requestData: ChatCompletionRequest | CompletionRequest | EmbeddingRequest,
        request: Request,
        stream_client: httpx.AsyncClient,
        add_stream: bool = True,
    ) -> Tuple[httpx.Request, LLMModel]:
        headers = request.headers.mutablecopy()
        path = request.url.path
        method = request.method
        content = await request.body()
        body = content.decode()
        model: LLMModel = self.parse_body(requestData)
        # Update the request path
        # TODO: Need to handle model not found error!
        url = httpx.URL(path=model.path + path)
        # Add the API Key for the inference server
        headers["Authorization"] = self.inference_apikey
        headers["host"] = llm_url
        if add_stream:
            body_dict = json.loads(body)
            if not "stream_options" in body_dict:
                body_dict["stream_options"] = {}
            if not "include_usage" in body_dict["stream_options"]:
                body_dict["stream_options"]["include_usage"] = True
            body = json.dumps(body_dict)
        # extract the body for forwarding.
        req = stream_client.build_request(
            method,
            url,
            headers=headers,
            content=body,
            # TODO: Might need to increase this timeout
            timeout=300.0,
        )

        return req, model

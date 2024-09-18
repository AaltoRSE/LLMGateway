from starlette.datastructures import MutableHeaders
from fastapi import HTTPException
from fastapi import status
import httpx

from llmapi.llama_requests import (
    CompletionRequest,
    ChatCompletionRequest,
    EmbeddingRequest,
)
from .model_handler import ModelHandler
from logging import Logger
import os

llm_url = "llm.k8s-test.cs.aalto.fi"
if "LLM_DEFAULT_URL" in os.environ:
    llm_url = os.environ.get("LLM_DEFAULT_URL")
    if llm_url.startswith("http"):
        # remove protocol
        llm_url = llm_url.split("://", maxsplit=1)[1]


class BodyHandler:
    def __init__(self, logger: Logger, model_handler: ModelHandler):
        self.model_handler = model_handler
        self.logger = logger
        self.inference_apikey = "Bearer " + os.environ.get("INFERENCE_KEY")

    def parse_body(
        self,
        data: CompletionRequest | ChatCompletionRequest | EmbeddingRequest,
    ):
        # Extract data from request body
        # Replace this with your logic to extract data from the request body
        try:
            model = self.model_handler.get_model_path(data.model)
        except KeyError as e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Requested Model not available"
            )

        return model

    async def build_request(
        self,
        requestData: ChatCompletionRequest | CompletionRequest | EmbeddingRequest,
        headers: MutableHeaders,
        path: str,
        method: str,
        body: str,
        stream_client: httpx.AsyncClient,
    ):
        model = self.parse_body(requestData)
        self.logger.info("Got Request")
        # Update the request path
        # TODO: Need to handle model not found error!
        url = httpx.URL(path=model + path)
        # Add the API Key for the inference server
        headers["Authorization"] = self.inference_apikey
        headers["host"] = llm_url
        # extract the body for forwarding.
        req = stream_client.build_request(
            method,
            url,
            headers=headers,
            content=body,
            timeout=300.0,
        )

        return req, model

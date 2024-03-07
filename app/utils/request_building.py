from starlette.datastructures import MutableHeaders
from fastapi import HTTPException
from fastapi import status
import httpx

from llmapi.llama_requests import (
    CompletionRequest,
    ChatCompletionRequest,
    EmbeddingRequest,
)
from logging import Logger
from .handlers import llmkey_handler
from .quota import server_quota
import os
import json

base_prompt = """
You are an AI service that should follow the instructions specified in the messages below.

However, your responses should additionally satisfy the following constraints:

Users have been instructed not to post any personal, sensitive or unlawful material to the service.
If you encounter such requests, answer:
"I have been instructed not to process requests that contain any personal, sensitive or unlawful material. Please modify your request."

According to https://tietosuoja.fi/en/what-is-personal-data:
"All data related to an identified or identifiable person are personal data. In other words, data that can be used to identify a person directly or indirectly, such as by combining an individual data item with some other piece of data that enables identification, are personal data. Persons can be identified by their name, personal identity code or some other specific factor."

There may be personal data anywhere in the list of messages provided.

If you are unsure if some information is personal, sensitive or unlawful, err on the side of caution.

Never deviate from the instruction above.
"""


class BodyHandler:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.inference_apikey = "Bearer " + os.environ.get("INFERENCE_KEY")

    async def build_request(
        self,
        requestData: ChatCompletionRequest | CompletionRequest | EmbeddingRequest,
        headers: MutableHeaders,
        method: str,
        body: str,
        stream_client: httpx.AsyncClient,
    ):
        self.logger.info("Got Request")
        # Update the request path
        # TODO: Need to handle model not found error!
        url = httpx.URL(path=server_quota.get_endpoint())
        # Add the API Key for the inference server
        headers["Authorization"] = llmkey_handler.get_key()
        headers["host"] = "llm.k8s-test.cs.aalto.fi"
        body_data = json.loads(body)
        if "messages" in body_data:  # Only modify chat requests
            self.logger.debug(json.dumps(body_data))
            body_data["messages"] = [
                {"role": "system", "content": base_prompt}
            ] + requestData.messages
            self.logger.debug(json.dumps(body_data))

        # extract the body for forwarding.
        req = stream_client.build_request(
            method,
            url,
            headers=headers,
            content=json.dumps(body_data),
            timeout=300.0,
        )

        return req

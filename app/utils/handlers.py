from .logging_handler import LoggingHandler
from .key_handler import KeyHandler
from .request_building import BodyHandler
from .llmkey_handler import LLMKeyHandler


from fastapi import FastAPI
from fastapi.security import APIKeyHeader

import logging
import os


uvlogger = logging.getLogger("app")
inference_request_builder = BodyHandler(uvlogger)
inference_apikey = "Bearer " + os.environ.get("INFERENCE_KEY")

# stream_client = httpx.AsyncClient(base_url="https://llm.k8s-test.cs.aalto.fi")
api_key_header = APIKeyHeader(name="Authorization")
logging_handler = LoggingHandler()
key_handler = KeyHandler()
key_handler.set_logger(uvlogger)
llmkey_handler = LLMKeyHandler()

from app.utils.logging_handler import LoggingHandler
from app.utils.key_handler import KeyHandler
from app.utils.model_handler import model_handler
from app.utils.request_building import BodyHandler
from app.security.session import SessionHandler
from contextlib import asynccontextmanager


from fastapi import FastAPI
from fastapi.security import APIKeyHeader

import logging
import os
import httpx

uvlogger = logging.getLogger("app")
inference_request_builder = BodyHandler(uvlogger, model_handler)
inference_apikey = "Bearer " + os.environ.get("INFERENCE_KEY")

# stream_client = httpx.AsyncClient(base_url="https://llm.k8s-test.cs.aalto.fi")
api_key_header = APIKeyHeader(name="Authorization")
logging_handler = LoggingHandler()
session_handler = SessionHandler()
key_handler = KeyHandler()
key_handler.set_logger(uvlogger)

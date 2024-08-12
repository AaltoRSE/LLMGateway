from server_logging.logging_handler import LoggingHandler
from .key_handler import KeyHandler
from .model_handler import model_handler
from .request_building import BodyHandler
from .admin_handler import AdminHandler
from security.session import SessionHandler


from fastapi import FastAPI
from fastapi.security import APIKeyHeader

import logging
import os

uvlogger = logging.getLogger("app")
inference_request_builder = BodyHandler(uvlogger, model_handler)
inference_apikey = "Bearer " + os.environ.get("INFERENCE_KEY")

testing = "PYTEST_CURRENT_TEST" in os.environ

api_key_header = APIKeyHeader(name="Authorization")
logging_handler = LoggingHandler(testing)
session_handler = SessionHandler(testing)
admin_handler = AdminHandler(testing)
key_handler = KeyHandler(testing)
key_handler.set_logger(uvlogger)

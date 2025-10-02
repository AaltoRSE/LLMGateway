"""
A placeholder hello world app.
"""

import os
import logging
import logging.config
from contextlib import asynccontextmanager

from typing import Any, AsyncGenerator
from fastapi import FastAPI, Depends
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
import httpx

from app.routers import (
    llm_router,
    saml_router,
    self_service_router,
    admin_router,
    auth_router,
)
from app.middleware.request_middleware import RequestContextLogMiddleware
from app.middleware.session_sanitize_middleware import SessionSanitizationMiddleWare
from app.static_files import SPAStaticFiles
from app.services.key_service import KeyService
from app.security.authentication_dependencies import authenticate_request
from app.security.entra_jwt import build_global_service
from app.dbs.redis.redis import get_key_client, get_key_quota_client
from app.config.db import get_api_key_repo

# Initiaize Logging
logging.config.fileConfig("app/logging.conf", disable_existing_loggers=False)
uvlogger = logging.getLogger("app")
# Initialize keys for use in the app


DEBUGGING = int(os.environ.get("DEV_MODE", "0")) == 1
if DEBUGGING:
    uvlogger.setLevel(logging.DEBUG)
    uvlogger.debug("Debugging active")


async def init_keys() -> None:
    """
    Function to run init keys.
    """
    print(get_api_key_repo)

    key_service = KeyService(
        key_repository=get_api_key_repo(),
        key_db=await anext(get_key_client()),
        key_quota_db=await anext(get_key_quota_client()),
    )
    await key_service.init_keys()


httpx_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def startup(  # pylint: disable=unused-argument
    app_instance: FastAPI,
) -> AsyncGenerator[None, Any]:
    """
    Startup function
    """
    uvlogger.info("Starting up the app")
    uvlogger.info("Debug mode: %s", DEBUGGING)
    uvlogger.info("Initializing EntraJWT service: %s", DEBUGGING)
    build_global_service()
    if DEBUGGING:
        uvlogger.setLevel(logging.DEBUG)
        for handler in uvlogger.handlers:
            handler.setLevel(logging.DEBUG)
        uvlogger.debug("Debugging active")
    httpx_client = httpx.AsyncClient()
    uvlogger.debug("httpx client set up")
    app_instance.state.httpx_client = httpx_client
    uvlogger.debug(app_instance.state.httpx_client)
    await init_keys()
    yield
    await httpx_client.aclose()


app = FastAPI(
    lifespan=startup, debug=DEBUGGING, dependencies=[Depends(authenticate_request)]
)

# Set CORS Policy
cors_origings = [
    "https://localhost",
    "https://localhost:5173",
    "https://ai.aalto.fi",
    "https://ai-testing.aalto.fi",
]

# Middleware is wrapped "around" existing middleware. i.e. order
# of execution is done inverse to order of adding.

# Add CORS Middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origings,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middlewares Order of execution is from last to first for incoming requests

# This will remove / add the actual session Data
app.add_middleware(SessionSanitizationMiddleWare)

# Need a fixed session key to work with potentially multiple instances.
session_key = os.environ.get("SESSION_KEY")
assert session_key is not None

app.add_middleware(SessionMiddleware, secret_key=session_key, max_age=600)

# Add Request logging
app.add_middleware(RequestContextLogMiddleware)

app.include_router(llm_router.router)
app.include_router(self_service_router.router)
app.include_router(admin_router.router)
app.include_router(saml_router.router)
app.include_router(auth_router.router)

# This has to be the very last route!!
app.mount("/", SPAStaticFiles(directory="frontend/dist", html=True), name="FrontEnd")

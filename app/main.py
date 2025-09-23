"""
A placeholder hello world app.
"""

import logging
import os
import logging.config

logging.config.fileConfig("app/logging.conf", disable_existing_loggers=False)
uvlogger = logging.getLogger("app")


from fastapi import FastAPI, Request, Security
from contextlib import asynccontextmanager

from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware


from app.routers import (
    llm_router,
    saml_router,
    self_service_router,
    admin_router,
    user_router,
    auth_router,
)
from app.utils.serverlogging import RouterLogging
from app.middleware.session_sanitize_middleware import SessionSanitizationMiddleWare
from app.static_files import SPAStaticFiles
from app.services.key_service import KeyService

from app.dbs.redis.redis import get_key_client, get_key_quota_client

# Initiaize services

# Initialize keys for use in the app


debugging = True

uvlogger.info("Starting up the app")


@asynccontextmanager
async def startup(app: FastAPI):
    from app.config.db import get_api_key_repo

    key_service = KeyService(
        key_repository=get_api_key_repo(),
        key_db=await anext(get_key_client()),
        key_quota_db=await anext(get_key_quota_client()),
    )
    await key_service.init_keys()
    yield


app = FastAPI(lifespan=startup, debug=True)

# Middleware is wrapped "around" existing middleware. i.e. order of execution is done inverse to order of adding.

# Set CORS Policy
cors_origings = [
    "https://localhost",
    "https://localhost:5173",
    "https://ai.aalto.fi",
    "https://ai-testing.aalto.fi",
]

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
app.add_middleware(SessionMiddleware, secret_key=session_key, max_age=600)

# Add Request logging
app.add_middleware(RouterLogging, logger=uvlogger, debug=debugging)

app.include_router(llm_router.router)
app.include_router(self_service_router.router)
app.include_router(admin_router.router)
app.include_router(saml_router.router)
app.include_router(user_router.router)
app.include_router(auth_router.router)

# This has to be the very last route!!
app.mount("/", SPAStaticFiles(directory="frontend/dist", html=True), name="FrontEnd")

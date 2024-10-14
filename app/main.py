"""
A placeholder hello world app.
"""

import logging
import os

logging.config.fileConfig("app/logging.conf", disable_existing_loggers=False)
uvlogger = logging.getLogger("app")


from fastapi import FastAPI, Request, Security


from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.utils.serverlogging import RouterLogging
from app.routers.llm_router import lifespan
from app.middleware.authentication_middleware import SessionAuthenticationBackend
from app.middleware.session_middleware import StorageSessionMiddleware
from app.static_files import SPAStaticFiles
from app.security.auth import get_user, BackendUser
from app.services.key_service import KeyService
from app.services.model_service import ModelService
from app.services.user_service import UserService

# Initiaize services

# Initialize keys for use in the app
key_service = KeyService()
key_service.init_keys()
# Initialize Models for use in the app
model_service = ModelService()
model_service.init_models()
# Initialize Users for use in the app
user_service = UserService()
user_service.init_user_db()


debugging = True

uvlogger.info("Starting up the app")
app = FastAPI(lifespan=lifespan, debug=True)

# Middleware is wrapped "around" existing middleware. i.e. order of execution is done inverse to order of adding.

# Set CORS Policy
cors_origings = [
    "https://localhost",
    "https://localhost:5173",
    "https://ai.aalto.fi",
    "https://ai-testing.aalto.fi",
]
# This covers all feature-branch deployments of aalto ai assistant
cors_regex = (
    "https://ashy-ground-060e46403-(.+)\\.westeurope\\.4\\.azurestaticapps\\.net"
)

# Add CORS Middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origings,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Allow everything from ai.aalto.fi and ai-testing.aalto.fi
    allow_origin_regex=cors_regex,
)


app.add_middleware(
    AuthenticationMiddleware,
    backend=SessionAuthenticationBackend(),
)

# Need a fixed session key to work with potentially multiple instances.
session_key = os.environ.get("SESSION_KEY")

app.add_middleware(StorageSessionMiddleware, secret_key=session_key, max_age=600)


# Add Request logging
app.add_middleware(RouterLogging, logger=uvlogger, debug=debugging)

from app.routers.llm_router import router as llm_router

app.include_router(llm_router)

from app.routers.self_service_router import router as self_service_router

app.include_router(self_service_router)

from app.routers.admin_router import router as admin_router

app.include_router(admin_router)

from app.routers.auth_router import router as saml_router

app.include_router(saml_router)


@app.get("/auth/test")
@app.post("/auth/test")
async def auth_test(
    request: Request,
):
    # Obtain the auth manually here, because we want to provide
    # Information about the authentication status, and using security would make this fail with Unauthorized
    # Responses...
    if request.user.is_authenticated:
        return {
            "authed": True,
            "user": request.user.username,
            "agreement_ok": request.user.agreement_ok,
            "admin": request.user.is_admin(),
        }
    else:
        return {"authed": False, "reason": "No user authenticated"}


@app.get("/data")
async def getData(request: Request, user: BackendUser = Security(get_user)):
    if user.is_authenticated:
        return user.get_user_data()
    else:
        return {"data": "No Data"}


# This has to be the very last route!!
app.mount("/", SPAStaticFiles(directory="dist", html=True), name="FrontEnd")

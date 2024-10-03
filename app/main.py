"""
A placeholder hello world app.
"""

import logging

logging.config.fileConfig("app/logging.conf", disable_existing_loggers=False)
uvlogger = logging.getLogger("app")


from fastapi import FastAPI, Request, Security


from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.saml.saml_router import get_authed_user
from app.utils.serverlogging import RouterLogging
from app.llmapi.llm_router import lifespan
from app.security.auth import SAMLSessionBackend
from app.security.session import SessionHandler
from app.static_files import SPAStaticFiles


debugging = True

from app.utils.handlers import session_handler

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
    AuthenticationMiddleware, backend=SAMLSessionBackend(session_handler)
)

app.add_middleware(SessionMiddleware, secret_key="some-random-string", max_age=None)

# Add Request logging
app.add_middleware(RouterLogging, logger=uvlogger, debug=debugging)

from app.llmapi.llm_router import router as llm_router

app.include_router(llm_router)

from app.selfservice.self_service_router import router as self_service_router

app.include_router(self_service_router)

from app.admin.admin_router import router as admin_router

app.include_router(admin_router)

from app.saml.saml_router import router as saml_router

app.include_router(saml_router)


@app.post("/auth/test")
async def auth_test(request: Request):
    # Obtain the auth manually here, because we want to provide
    # Information about the authentication status, and using security would make this fail with Unauthorized
    # Responses...
    if request.user.is_authenticated:
        return {"authed": True, "user": request.user.username}
    else:
        return {"authed": False, "reason": "No Token provided"}


@app.get("/data")
async def getData(request: Request, user: any = Security(get_authed_user)):
    if user.is_authenticated:
        return user.get_user_data()
    else:
        return {"data": "No Data"}


# This has to be the very last route!!
app.mount("/", SPAStaticFiles(directory="dist", html=True), name="FrontEnd")

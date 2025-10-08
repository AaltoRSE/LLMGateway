from typing import Any, AsyncGenerator
import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager
import httpx

from app.services.key_service import KeyService
from app.security.entra_jwt import build_global_service
from app.dbs.redis.redis import get_key_client, get_key_quota_client
from app.config.db import get_api_key_repo
from app.config import DEBUGGING


logger = logging.getLogger("app")


async def init_keys() -> None:
    """
    Function to run init keys.
    """
    key_service = KeyService(
        key_repository=get_api_key_repo(),
        key_db=await anext(get_key_client()),
        key_quota_db=await anext(get_key_quota_client()),
    )
    await key_service.init_keys()


def set_debug_level() -> None:
    """
    Init for the debug logger levels.
    """
    logger.info("Debug mode: %s", DEBUGGING)
    if DEBUGGING:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("Debugging active")


def init_httpx_async_client(app_instance: FastAPI) -> httpx.AsyncClient:
    """
    Setup function for the httpx client
    """
    logger.info("httpx client set up")
    httpx_client = httpx.AsyncClient(timeout=600)
    app_instance.state.httpx_client = httpx_client
    return httpx_client


@asynccontextmanager
async def startup(
    app_instance: FastAPI,
) -> AsyncGenerator[None, Any]:
    """
    Startup function
    """
    logger.info("Starting up the app")
    logger.info("Initializing EntraJWT service: %s")
    build_global_service()
    set_debug_level()
    # We set a very high timeout here, since there is always
    # the possibility that a model needs to load first, which
    # takes substantial time.
    client = init_httpx_async_client(app_instance)
    await init_keys()
    yield
    await client.aclose()

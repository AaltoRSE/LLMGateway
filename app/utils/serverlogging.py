from starlette.middleware.base import BaseHTTPMiddleware
import logging
import typing
from fastapi import FastAPI, Request, Response


class RouterLogging(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, *, logger: logging.Logger) -> None:
        self._logger = logger
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        self._logger.debug("{}: {}".format(request.method, str(request.url)))
        return await call_next(request)

from starlette.middleware.base import BaseHTTPMiddleware
import logging
import typing
from fastapi import FastAPI, Request, Response

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]


class RouterLogging(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, *, logger: logging.Logger) -> None:
        self._logger = logger
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        self.logger.debug("{}: {}", request.method, request.url)
        return call_next(request)

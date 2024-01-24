from starlette.middleware.base import BaseHTTPMiddleware
import logging
import typing
from fastapi import FastAPI, Request, Response


class RouterLogging(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, *, logger: logging.Logger, debug=True) -> None:
        self._logger = logger
        self.debug = debug
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        self._logger.debug("{}: {}".format(request.method, str(request.url)))
        # TODO: Need to deactivate once this actually gets into production!
        if self.debug:
            self._logger.debug(await request.body())
        return await call_next(request)

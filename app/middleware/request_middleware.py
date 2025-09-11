""" This module contains middleware for correlation ID logging """

from __future__ import annotations
import logging
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.util.cef_logger import CEFRequestLogger


logger = logging.getLogger("app")

cef_logger = CEFRequestLogger()

CORRELATION_ID_HEADER = "X-Correlation-Id"

class RequestContextLogMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request.state.correlation_id = str(uuid4())
        # might have no effect, but for extra security it can't be injected from outside
        request.scope["user"] = None
        start_time = datetime.now()

        try:
            response: Response = await call_next(request)
        except Exception as e:  # pylint: disable=broad-except
            if isinstance(e, HTTPException):
                # HTTP Exceptions are re-raise, as those are expected exceptions.
                response = JSONResponse(
                    status_code=e.status_code, content={"detail": e.detail}
                )
            else:
                # Newlines added here, since the traceback will automatically insert newlines anyways.
                logger.exception(
                    "Issue with id %s \n %s",
                    request.state.correlation_id,
                    str(e),
                )

                response = JSONResponse(
                    status_code=500,
                    content={
                        "detail": f"Internal server error, request correlation ID: '{request.state.correlation_id}'. "
                        + "Please contact support with the correlation ID, if the problems persists."
                    },
                )

        # Continue logging the query
        end_time = datetime.now()

        # Log the request
        cef_logger.log(
            correlation_id=request.state.correlation_id,
            request=request,
            response=response,
            start_time=start_time,
            end_time=end_time,
            authenticated_user=request.user
        )

        # Set response headers
        response.headers[CORRELATION_ID_HEADER] = request.state.correlation_id

        return response

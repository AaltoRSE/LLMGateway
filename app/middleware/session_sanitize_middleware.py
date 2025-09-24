from starlette.requests import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
    Response,
)
from app.services.session_service import SessionService
from app.schemas.session_schema import HTTPSession, SESSION_DATA_FIELD
import app.dbs.redis.redis
from typing import Any


class SessionSanitizationMiddleWare(BaseHTTPMiddleware):
    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        super().__init__(*args, **kwargs)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # load a session service to interact with the redis db.
        session_service = SessionService(
            await anext(app.dbs.redis.redis.get_session_client())
        )
        scope = request.scope
        if "session" in scope:
            session: dict = scope["session"]

            key = session.get("key", None)
            if key is not None:
                session_data = await session_service.get_session(key)
                session[SESSION_DATA_FIELD] = session_data
            else:
                scope["session"] = {}
        response = await call_next(request)

        # This feels a bit odd, but I think we just have to
        # clean up the scope here...
        if SESSION_DATA_FIELD in session:
            session.pop(SESSION_DATA_FIELD)

        return response

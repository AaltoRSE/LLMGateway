from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.services.session_service import SessionService
from app.models.session import HTTPSession, SESSION_DATA_FIELD


def get_session(request: Request) -> HTTPSession:
    session = request.scope["session"]
    if SESSION_DATA_FIELD in session:
        return session[SESSION_DATA_FIELD]
    else:
        return None


class SessionSanitizationMiddleWare(BaseHTTPMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_service = SessionService()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        scope = request.scope
        if "session" in scope:
            session: dict = scope["session"]

            key = session.get("key", None)
            if key is not None:
                session_data = await self.session_service.get_session(key)
                session[SESSION_DATA_FIELD] = session_data
            else:
                scope["session"] = {}
        response = await call_next(request)

        # This feels a bit odd, but I think we just have to
        # clean up the scope here...
        if SESSION_DATA_FIELD in session:
            session.pop(SESSION_DATA_FIELD)

        return response

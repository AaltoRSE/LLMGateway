from starlette.middleware.sessions import SessionMiddleware
from starlette.types import Receive, Scope, Send
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import Message, Receive, Scope, Send
from fastapi import Request
import logging

import json
from base64 import b64decode, b64encode
from itsdangerous.exc import BadSignature
from app.services.session_service import SessionService
from app.models.session import HTTPSession, SESSION_DATA_FIELD

logger = logging.getLogger(__name__)


def get_session(request: Request) -> HTTPSession:
    session = request.scope["session"]
    if SESSION_DATA_FIELD in session:
        return session[SESSION_DATA_FIELD]
    else:
        return None


class StorageSessionMiddleware(SessionMiddleware):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_service = SessionService()

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        initial_session_was_empty = True

        if self.session_cookie in connection.cookies:
            data = connection.cookies[self.session_cookie].encode("utf-8")
            try:
                data = self.signer.unsign(data, max_age=self.max_age)
                scope["session"] = json.loads(b64decode(data))
                # Load additional data from the session service
                logger.info(f"Found session data: {scope['session']}")
                key = scope["session"].get("key")
                if key:
                    session_data = self.session_service.get_session(key)
                    if session_data:
                        logger.info("Found session data")
                        scope["session"][SESSION_DATA_FIELD] = session_data
                    else:
                        # Eliminate the whole session!
                        logger.info("Invalid session data")
                        scope["session"] = {}
                initial_session_was_empty = False
            except BadSignature as e:
                logger.info("Invalid session data")
                logger.info(e)
                scope["session"] = {}
        else:
            scope["session"] = {}
            logger.info("No cookie found")

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                # Persist session data.
                if scope["session"]:
                    # We remove the session data.
                    if SESSION_DATA_FIELD in scope["session"]:
                        # Remove internal data, which should always be in here
                        scope["session"].pop(SESSION_DATA_FIELD, None)
                    session_data = scope["session"]
                    logger.info(f"Setting session data to {scope['session']}")
                    data = b64encode(json.dumps(session_data).encode("utf-8"))
                    data = self.signer.sign(data)
                    headers = MutableHeaders(scope=message)
                    header_value = "{session_cookie}={data}; path={path}; {max_age}{security_flags}".format(  # noqa E501
                        session_cookie=self.session_cookie,
                        data=data.decode("utf-8"),
                        path=self.path,
                        max_age=f"Max-Age={self.max_age}; " if self.max_age else "",
                        security_flags=self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
                elif not initial_session_was_empty:
                    # The session has been cleared.
                    headers = MutableHeaders(scope=message)
                    header_value = "{session_cookie}={data}; path={path}; {expires}{security_flags}".format(  # noqa E501
                        session_cookie=self.session_cookie,
                        data="null",
                        path=self.path,
                        expires="expires=Thu, 01 Jan 1970 00:00:00 GMT; ",
                        security_flags=self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
            await send(message)

        await self.app(scope, receive, send_wrapper)

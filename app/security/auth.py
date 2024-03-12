from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
    BaseUser,
)
from starlette.requests import HTTPConnection
from starlette.middleware import Middleware
from .session import SessionHandler
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


def get_request_source(request: HTTPConnection):    
    # We asume, that we can either be only reached via proxy ( first option ), or are directly accessed from clients.
    if "x-forwarded-for" in request.headers:
        # Take the latest (we trust this one) header...
        return request.headers["x-forwarded-for"].split(",")[-1]
    else:
        return request.client.host


class SAMLUser(SimpleUser):
    def __init__(self, username: str, userdata: dict):
        self.username = username
        self.data = userdata

    def get_user_data(self):
        return self.data


class SAMLSessionBackend(AuthenticationBackend):
    def __init__(self, session_handler: SessionHandler):
        self.session_handler = session_handler

    async def authenticate(self, conn):
        try:
            if conn.session == None:
                return
        except AssertionError:
            return

        # check for authentication:
        if not "key" in conn.session:
            return
        try:
            data = self.session_handler.get_session_data(conn.session["key"])
            # Check IP correct
            if data == None:
                # This is not a valid session any more... so we need to reset it somehow.
                clean_session(conn.session)
                return
            if data["UserIP"] != get_request_source(conn):
                logger.info(f"Request IP is {get_request_source(conn)} while sored IP for session was {data["UserIP"]}" )
                return
        except HTTPException:
            return
        return AuthCredentials(["authenticated"]), SAMLUser(data["UserName"], data)


def clean_session(session):
    session.pop("key")
    session["invalid"] = True

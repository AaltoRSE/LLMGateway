from starlette.authentication import AuthCredentials, AuthenticationBackend
from starlette.requests import HTTPConnection
from fastapi import HTTPException

import logging

# Unfortunately we need to import the whole stack here, as FastAPI dependency injection
# does not work with starlette middlewares.
from app.services.session_service import SessionService
from app.models.session import SESSION_DATA_FIELD, HTTPSession

logger = logging.getLogger(__name__)

session_handler = SessionService()

from app.security.auth import get_request_source, BackendUser


# This is a simple backend for SAML authentication.
class SessionAuthenticationBackend(AuthenticationBackend):
    def __init__(self):
        pass

    async def authenticate(self, conn: HTTPConnection):
        # We need to set up our connection...

        try:
            if conn.session == None:
                return
        except AssertionError:
            return
        logger.debug("Trying to authenticate a user")
        # Check if this session has a key (The session validity is checked by the session handler,
        # so if the session is valid, than the key value we stored is also valid)
        if not "key" in conn.session:
            # There is no key, so there is no auth.
            logger.debug("No key in session -> No User")
            return
        try:
            # Try to get the stored data for the session
            session: HTTPSession = conn["session"][SESSION_DATA_FIELD]

            # Check IP correct
            if session.data == None:
                logger.debug("No Data in session -> No User")
                # This is not a valid session any more... so we need to reset it somehow.
                session_handler.delete_session(session.key)
                return
            if session.ip != get_request_source(conn):
                logger.debug(
                    f"Request IP is {get_request_source(conn)} while stored IP for session was {session.ip}"
                )
                return
        except HTTPException as e:
            logger.debug("Exception -> No User")
            logger.error(e)
            return
        # TODO: We might want to add the option to distinguish between employees and students here.
        # To do so, we will need to obtain the role of the current data["UserName"] from somewhere, maybe we need it from HAKA......

        currentUser = BackendUser(
            username=session.user,
            userdata=session.data,
            roles=session.roles,
            isadmin=session.admin,
        )
        return AuthCredentials(["authenticated"]), currentUser

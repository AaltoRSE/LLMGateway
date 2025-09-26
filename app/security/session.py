from typing import Annotated
import logging

from starlette.requests import HTTPConnection
from fastapi import HTTPException, Depends, Request

from app.security.auth import BackendUser, get_request_source, RequestSource

from app.services.session_service import SessionService
from app.services.user_service import UserService

from app.schemas.session_schema import SESSION_DATA_FIELD, HTTPSession

logger = logging.getLogger(__name__)


def get_session(request: Request) -> HTTPSession | None:
    session = request.scope["session"]
    if SESSION_DATA_FIELD in session:
        return session[SESSION_DATA_FIELD]
    else:
        return None


class SessionBasedAuthScheme:
    def __init__(
        self, session_service: SessionService, user_service: UserService
    ) -> None:
        self.session_service = session_service
        self.user_service = user_service


async def get_user_from_session(
    conn: HTTPConnection,
    session_handler: Annotated[SessionService, Depends(SessionService)],
) -> BackendUser | None:
    try:
        if conn.session is None:
            logger.debug("No session in connection")
            return None
    except AssertionError:
        return None
    logger.debug("Trying to authenticate a user")
    # Check if this session has a key (The session validity is checked by the session handler,
    # so if the session is valid, than the key value we stored is also valid)
    if not "key" in conn.session:
        # There is no key, so there is no auth.
        logger.debug("No key in session -> No User")
        return None
    try:
        # Try to get the stored data for the session
        session: HTTPSession = conn["session"][SESSION_DATA_FIELD]
        if session is None:
            logger.debug("No valid session detected.")
            return None
        # Check IP correct
        if session.data == None:
            logger.debug("No Data in session -> No User")
            # This is not a valid session any more... so we need to reset it somehow.
            await session_handler.delete_session(session.key)
            return None
        if session.ip != get_request_source(conn):
            logger.debug(
                f"Request IP is {get_request_source(conn)} while stored IP for session was {session.ip}"
            )
            # Invalid access to the session. We will delete it.
            await session_handler.delete_session(session.key)

            return None
    except HTTPException as e:
        logger.debug("Exception -> No User")
        logger.error(e)
        return None
    currentUser = BackendUser(
        username=session.user_id,
        request_source=RequestSource(user_id=session.user_id, has_session=True),
        userdata=session.data,
        roles=session.roles,
        isadmin=session.admin,
        agreement_ok=session.agreement_ok,
        quota=session.quota,
    )
    return currentUser

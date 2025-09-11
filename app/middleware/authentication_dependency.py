from starlette.authentication import AuthCredentials, AuthenticationBackend
from starlette.requests import HTTPConnection
from fastapi import HTTPException, Request, Depends
from fastapi.security import APIKeyHeader
import logging

# Unfortunately we need to import the whole stack here, as FastAPI dependency injection
# does not work with starlette middlewares.
from app.services.session_service import SessionService
from app.models.session import SESSION_DATA_FIELD, HTTPSession

logger = logging.getLogger(__name__)

from app.security.auth import get_request_source, BackendUser


api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
admin_key_header = APIKeyHeader(name="AdminKey", auto_error=False)
def authenticate_request(self, conn : HTTPConnection, api_key : str = Depends(api_key_header), admin_key : str = Depends(admin_key_header), session_handler : SessionService = Depends(SessionService) ):
    api_key_user = 1
    
    session_user = get_user_from_session(conn, session_handler)
    
    pass

def get_user_from_session(conn : HTTPConnection, session_handler : SessionService):        
        try:
            if conn.session == None:
                logger.debug("No session in connection")
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
                # Invalid access to the session. We will delete it. 
                session_handler.delete_session(session.key)                

                return
        except HTTPException as e:
            logger.debug("Exception -> No User")
            logger.error(e)
            return
        currentUser = BackendUser(
            username=session.user,
            userdata=session.data,
            roles=session.roles,
            isadmin=session.admin,
            agreement_ok=session.agreement_ok,
        )
        return currentUser
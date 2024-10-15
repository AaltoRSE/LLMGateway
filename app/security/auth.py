from starlette.requests import HTTPConnection
from starlette.authentication import AuthenticationBackend, SimpleUser
from fastapi import Request, HTTPException, status, Response
from fastapi.responses import RedirectResponse, HTMLResponse

import logging
import os
import json

# Unfortunately we need to import the whole stack here, as FastAPI dependency injection
# does not work with starlette middlewares.

from app.models.session import HTTPSession
from app.services.session_service import SessionService


from typing import Tuple, Union, Callable, Dict, List

logger = logging.getLogger(__name__)
frontend_url = os.getenv("FRONTEND_URL", "/")

is_proxied = os.getenv("REQUEST_PROXIED", False) == "True"


def get_request_source(request: HTTPConnection):
    # We asume, that we can either be only reached via proxy ( first option ), or are directly accessed from clients.
    if is_proxied:
        # This assumes that our proxy has set this header
        return request.headers["x-forwarded-for"]
    else:
        return request.client.host


def clean_session(session):
    # Remove the key data from the session.
    session.pop("key")
    # and explicitly mark the session as invalid.
    session["invalid"] = True


class SessionBasedAuthScheme:
    def __init__(self, session_service, user_service):
        self.session_service = session_service
        self.user_service = user_service


class AaltoBackendAuthentication:
    def __init__(
        self,
    ):
        pass

    def getAuthenticationBackend(self) -> AuthenticationBackend:
        raise NotImplementedError()


class BackendUser(SimpleUser):
    def __init__(
        self,
        username: str,
        userdata: dict,
        roles: List[str],
        isadmin: bool,
        agreement_ok: bool,
    ):
        super().__init__(username)
        self.admin = isadmin
        self.agreement_ok = agreement_ok
        self.data = userdata
        self.role = roles

    def get_user_data(self):
        return self.data

    def is_admin(self):
        return self.admin


class BackendAuthenticator:
    def __init__(self):
        pass

    def login(
        self,
        request: Request,
        create_session: Callable[[Dict], None],
    ) -> Tuple[Response, Union[HTTPSession, None]]:
        """
        Login the user. This can either be a direct login or a redirect.
        You can write additional information into the session object, but make sure that this
        information is not sensitive. Also, the "key" field is reserved for the app.
        If authentication is successfull, a session needs to be created with the
        Must return a response and, if authentication was successful, the session key, otherwise None.

        Args:
              request (Request): The request object.
              create_session (Callable[[Dict], None]): The function to create a session, must be provided with a dictionary that contains at least the following fields:
              - 'auth_name' , the unique ID of the user in the auth scheme, must stay constant
              - 'groups', the groups the user is in, for permission management
              - 'first_name', the first name of the user
              - 'last_name', the last name of the user
              These fields will be used to compare against the user database and fill in permissions and user information.
        """
        return HTTPException(status_code=404, detail="Not implemented")

    async def login_callback(
        self,
        request: Request,
        create_session: Callable[[Dict], None],
    ) -> HTTPSession:
        """
        Callback function for the authentication.
        Must return the session object generated by the login callback.
        Essentially this function must finalize the authentication process.
        Further redirects are handled by the router.
        Args:
              request (Request): The request object.
              create_session (Callable[[Dict], None]): The function to create a session, must be provided with a dictionary that contains at least the following fields:
              - 'auth_name' , the unique ID of the user in the auth scheme, must stay constant
              - 'groups', the groups the user is in, for permission management
              - 'first_name', the first name of the user
              - 'last_name', the last name of the user
              These fields will be used to compare against the user database and fill in permissions and user information.
        """
        return HTTPException(status_code=404, detail="Not implemented")

    async def metadata() -> Response:
        """
        Optional Metadata endpoint. Depends on the auth scheme.
        """
        return HTTPException(status_code=404, detail="Not implemented")

    async def logout(
        self,
        request: Request,
        user: BackendUser,
        delete_session_callback: Callable,
    ) -> Union[RedirectResponse, None]:
        """
        Logout endpoint, either forwards to a single logout service or
        just logs out the user.
        If the response is not a redirect response, the session will be cleaned
        up by the router. Make sure, that the auth scheme doesn't keep any data
        in the session.
        """
        return HTTPException(status_code=404, detail="Not implemented")

    async def logout_callback(
        request: Request,
        user: BackendUser,
        delete_session_callback: Callable,
    ):
        """
        Logout callback endpoint, for callbacks from a single logout scheme.
        This function only needs to clean up anything that's inherent for the used authentication scheme.
        The user data (i.e. the data stored in the session) is available through user.get_user_data().
        The actual session will be terminated by the router regardless on the outcomes of this function.
        """
        return HTTPException(status_code=404, detail="Not implemented")


def get_user(conn: HTTPConnection) -> BackendUser:
    """
    Get the authenticated user from the given HTTPConnection.

    Parameters:
    - conn (HTTPConnection): The HTTPConnection object representing the current connection.

    Raises:
    - HTTPException: If no user is authenticated, a 403 Forbidden status is raised with the detail "No user authenticated".

    Returns:
    - User: The authenticated user object retrieved from the connection.
    """
    logger.debug(conn.user)
    logger.debug(conn.session)
    if conn.user == None or not conn.user.is_authenticated:
        credentials_exception = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No user authenticated",
        )
        raise credentials_exception

    return conn.user


def get_admin_user(conn: HTTPConnection) -> BackendUser:
    """
    Get the admin user from the

    Parameters:
    - conn (HTTPConnection): The HTTPConnection object representing the current connection.

    Raises:
    - HTTPException: If no user or the user is not an admin a 403 Forbidden status is raised with the detail "No user authenticated or autheticated use rnot an admin".

    Returns:
    - User: The authenticated user object retrieved from the connection.
    """
    if conn.user == None or not conn.user.is_authenticated:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user authenticated",
        )
        raise credentials_exception
    user: BackendUser = conn.user
    if not user.is_admin():
        credentials_exception = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not an admin",
        )
        raise credentials_exception
    return conn.user


def check_auth_response(
    request: Request,
    session: Union[HTTPSession, None],
    response: Union[Response, None],
):
    """
    Check, whether the request is a SAML request.
    """

    if response == None:
        check_auth_session(request, session)
        frontend_url = os.getenv("FRONTEND_URL")
        # redirect_url = request.session["redirect_url"]
        if "redirect_url" in request.session:
            # If we have a popup, which is the only way response is None here, we ignore any redirect url given.
            request.session.pop("redirect_url")
        logger.info(request.session)
        logger.info("Session created.")
        # TODO: This needs to be improved to make sure, that there are proper error messages displayed, if the postMessage cannot be called.
        return HTMLResponse(
            f"""
        <script>
            try {{
                window.opener.postMessage("Logged In", "{frontend_url}");
                window.close();
            }} catch (error) {{
                if (error instanceof DOMException ) {{
                    document.body.innerHTML = "<h1>Invalid caller! Make sure this login is only accessed from {frontend_url}.</h1><p>Please contact support.</p>";
                }}
                console.error("postMessage failed:", error);
            }}
        </script>"""
        )
    else:
        if not session == None:
            request.session["key"] = session.key
        return response


def check_auth_session(request: Request, session: Union[HTTPSession, None]):
    logger.info(request.session)
    if session == None:
        logger.info("No session provided")
        raise HTTPException(403, "Not authenticated")
    # We now have an authed session, so we set the key in the session.
    logger.info("Setting session key")
    logger.info(session)
    request.session["key"] = session.key


def check_logout_response(
    request: Request, response: Union[Response, None], session_service: SessionService
):
    """
    Check, whether the logout was successful, or if this is a redirect.
    """
    if response == None:
        # We will clean up the session.
        clean_session(request, session_service)
        return RedirectResponse(url="/")
    else:
        return response


def clean_session(request: Request, session_service: SessionService):
    """
    Clean the session
    """
    session_key = request.session["key"]
    request.session["invalid"] = True
    if not session_key == None:
        request.session["key"] == None
        session_service.delete_session(session_key)


def sanitize_redirect(redirect: Union[str, None]) -> str:
    """
    Sanitize the redirect URL
    """
    # If no redirect, simply return startingpoint
    if redirect == None:
        return frontend_url
    # if the redirect is a calll to an API endpoint, we don't want that but redirect to the frontend
    if redirect.startswith("api"):
        return "/"
    # if the redirect is anything other than a path on this server, we don't want that either
    if not redirect.startswith("/"):
        return "/"
    return redirect

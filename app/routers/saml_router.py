from fastapi import (
    APIRouter,
    Request,
    Security,
    Depends,
    Query,
)
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from typing import Annotated


from app.security.authentication_dependencies import (
    requires_session,
    authenticate_request,
)
from app.security.auth import (
    get_request_source,
    check_auth_response,
    check_logout_response,
    sanitize_redirect,
    clean_session,
    frontend_url,
)
from app.security.auth import BackendUser
from app.security.saml import SAMLAuthenticator, HTTPSession
from app.services.session_service import SessionService, SessionAuthData
from app.services.user_service import UserService
import logging
import os


logger = logging.getLogger("app")

router = APIRouter(prefix="/saml", tags=["saml"])

auth_backend = SAMLAuthenticator()


@router.get("/login")
async def login(
    request: Request,
    session_service: Annotated[SessionService, Depends(SessionService)],
    user_service: Annotated[UserService, Depends(UserService)],
    redirect_url: str = Query(None, alias="redirect_uri"),
) -> Response | HTMLResponse:
    """
    Login endpoint
    """
    logger.debug(
        "Obtained redirect url was : " + ("" if redirect_url == None else redirect_url)
    )
    request.session["redirect_url"] = sanitize_redirect(redirect_url)
    logger.debug("Redirect URL has been set to: " + request.session["redirect_url"])
    source_ip = get_request_source(request)
    process_session_data = lambda session_data: session_service.create_session(
        session_data=session_data, source_ip=source_ip, user_service=user_service
    )
    response, session = await auth_backend.login(request, process_session_data)
    final_response = check_auth_response(request, session, response)
    return final_response


@router.post("/acs")
async def login_callback(
    request: Request,
    session_service: Annotated[SessionService, Depends(SessionService)],
    user_service: Annotated[UserService, Depends(UserService)],
) -> Response | HTMLResponse:
    """
    General callback endpoint
    """
    logger.debug("GETTING LOGIN Callback")
    logger.debug(request.session)
    source_ip = get_request_source(request)

    async def session_callback(session_data: SessionAuthData) -> HTTPSession:
        return await session_service.create_session(
            session_data=session_data, source_ip=source_ip, user_service=user_service
        )

    session = await auth_backend.login_callback(request, session_callback)
    logger.debug("Trying to build the response")
    if os.getenv("POPUPLOGIN") == "1":
        response = None
    else:
        response = RedirectResponse(
            url=(
                request.session["redirect_url"]
                if "redirect_url" in request.session
                else frontend_url
            ),
            status_code=303,
        )
    updated_response = check_auth_response(request, session, response)
    logger.debug(response)
    logger.debug(request.session)
    # This will redirect to the original page.
    return updated_response


@router.get("/metadata")
async def metadata() -> Response:
    """
    Optional Metadata endpoint. Depends on the auth scheme.
    """
    return await auth_backend.metadata()


@router.get("/logout")
async def saml_slo_logout(
    request: Request,
    session_service: Annotated[SessionService, Depends(SessionService)],
    user: BackendUser = Security(requires_session),
) -> Response | HTMLResponse:
    """
    Logout endpoint
    """

    async def delete_session() -> None:
        await clean_session(request=request, session_service=session_service)

    response = await auth_backend.logout(request, user, delete_session)
    return await check_logout_response(request, response, session_service)


@router.get("/sls")
async def saml_sls_logout(
    request: Request,
    session_service: Annotated[SessionService, Depends(SessionService)],
    user: BackendUser = Security(requires_session),
) -> Response | HTMLResponse:
    """
    Logout callback. If this is successfull, the users session is removed.
    """

    async def delete_session() -> None:
        await clean_session(request=request, session_service=session_service)

    await auth_backend.logout_callback(request, user, delete_session)
    # if it hasn't been cleaned, we will clean the session.
    return await check_logout_response(request, None, session_service)

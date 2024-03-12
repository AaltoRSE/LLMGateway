from fastapi import APIRouter, Request, Security, Response, HTTPException, status

from onelogin.saml2.auth import OneLogin_Saml2_Auth


from starlette.responses import RedirectResponse
from utils.handlers import session_handler

from security.saml import (
    saml_settings,
    prepare_from_fastapi_request,
    get_authed_user,
    decrypt_name_id,
)
from security.auth import clean_session, get_request_source

import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/saml", tags=["saml"])


@router.get("/login")
async def login(request: Request):
    """
    Login endpoint
    """
    req = await prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, saml_settings)
    callback_url = auth.login()
    response = RedirectResponse(url=callback_url)
    return response


@router.post("/acs")
async def saml_callback(request: Request):
    """
    General callback endpoint
    """
    logger.info("SAML Auth requested")
    req = await prepare_from_fastapi_request(request, True)
    auth = OneLogin_Saml2_Auth(req, saml_settings)
    auth.process_response()  # Process IdP response
    errors = auth.get_errors()  # This method receives an array with the errors
    logger.info("SAML processed")
    if len(errors) == 0:
        if not auth.is_authenticated():
            # This check if the response was ok and the user data retrieved or not (user authenticated)
            return "User Not authenticated"
        else:
            sessionData = {}
            sessionData["samlUserdata"] = auth.get_attributes()
            logger.debug(sessionData["samlUserdata"])
            # Now, we check, whether the user is an employee, and thus eligible to use the service
            debug = int(os.environ.get("GATEWAY_DEBUG", 0)) == 1
            logger.debug(debug)
            try:
                if (not debug) and (
                    not "employee"
                    in sessionData["samlUserdata"]["urn:oid:1.3.6.1.4.1.5923.1.1.1.1"]
                ):
                    raise HTTPException(
                        status.HTTP_403_FORBIDDEN,
                        "Only staff can use this self service",
                    )
            except Exception as e:
                logger.error(e)
                logger.debug(sessionData)
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Authentication invalid")
            sessionData["samlNameId"] = auth.get_nameid()
            sessionData["samlNameIdFormat"] = auth.get_nameid_format()
            sessionData["samlNameIdNameQualifier"] = auth.get_nameid_nq()
            sessionData["samlNameIdSPNameQualifier"] = auth.get_nameid_spnq()
            sessionData["samlSessionIndex"] = auth.get_session_index()
            sessionData["UserIP"] = get_request_source(request)
            logger.debug(sessionData)
            try:
                sessionData["UserName"] = sessionData["samlUserdata"][
                    "urn:oid:1.3.6.1.4.1.5923.1.1.1.6"
                ][0]
            except Exception as e:
                logger.error(e)
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "Authentication invalid, missing saml data",
                )
            session_key = session_handler.create_session(sessionData)
            logger.debug("Session key created, adding to request session")
            request.session["key"] = session_key
            request.session["invalid"] = False
            forwardAddress = f"/"
            logger.debug("Forwarding to /")
            return RedirectResponse(
                url=forwardAddress, status_code=status.HTTP_303_SEE_OTHER
            )
    else:
        logger.error(
            "Error when processing SAML Response: %s %s"
            % (", ".join(errors), auth.get_last_error_reason())
        )
        return "Error in callback"


@router.get("/metadata")
async def metadata():
    """
    Metadata endpoint
    """
    metadata = saml_settings.get_sp_metadata()
    return Response(content=metadata, media_type="text/xml")


@router.get("/slo")
async def saml_logout(request: Request, user: any = Security(get_authed_user)):
    """
    Logout endpoint
    """
    req = await prepare_from_fastapi_request(request, True)
    auth = OneLogin_Saml2_Auth(req, saml_settings)
    name_id = session_index = name_id_format = name_id_nq = name_id_spnq = None
    logger.info(user)
    userData = user.get_user_data()
    if "samlNameId" in userData:
        name_id = userData["samlNameId"]
    if "samlSessionIndex" in userData:
        session_index = userData["samlSessionIndex"]
    if "samlNameIdFormat" in userData:
        name_id_format = userData["samlNameIdFormat"]
    if "samlNameIdNameQualifier" in userData:
        name_id_nq = userData["samlNameIdNameQualifier"]
    if "samlNameIdSPNameQualifier" in userData:
        name_id_spnq = userData["samlNameIdSPNameQualifier"]
    url = auth.logout(
        name_id=name_id,
        session_index=session_index,
        nq=name_id_nq,
        name_id_format=name_id_format,
        spnq=name_id_spnq,
    )
    logger.info(f"Redirecting to {url}")
    request.session["LogoutRequestID"] = auth.get_last_request_id()
    return RedirectResponse(url=url)


@router.get("/sls")
async def saml_logout(request: Request, user: any = Security(get_authed_user)):
    """
    Single logout callback endpoint
    """
    req = await prepare_from_fastapi_request(request, True)
    auth = OneLogin_Saml2_Auth(req, saml_settings)
    logger.info(req)
    request_id = None
    if "LogoutRequestID" in request.session:
        request_id = request.session["LogoutRequestID"]
    logger.info(request_id)
    dscb = lambda: clean_session(request.session)
    url = auth.process_slo(request_id=request_id, delete_session_cb=dscb)
    logger.info(url)
    errors = auth.get_errors()
    logger.info(errors)
    if len(errors) == 0:
        logger.info("Redirecting")
        if url is not None:
            logger.info("Redirecting to indicated url")
            # To avoid 'Open Redirect' attacks, before execute the redirection confirm
            # the value of the url is a trusted URL.
            return RedirectResponse(url)
        else:
            logger.info("Redirecting to default")
            # Return back to main page
            return RedirectResponse(url="/")
    elif auth.get_settings().is_debug_active():
        logger.info("Got an error")
        error_reason = auth.get_last_error_reason()
        logger.info(error_reason)
        logger.info(auth._last_response)
        return error_reason
    else:
        logger.error(auth.get_last_error_reason())

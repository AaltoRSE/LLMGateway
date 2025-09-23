from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.auth import OneLogin_Saml2_Auth

from fastapi.responses import RedirectResponse
from app.security.auth import BackendAuthenticator
from app.schemas.user_schema import SessionAuthData

from typing import Callable, Dict, Awaitable
from fastapi import Request, Response, HTTPException
import xmlsec
import os
import logging

saml_logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
print(BASE_DIR)
SAML_DIR = os.path.join(BASE_DIR, "saml_data")
saml_logger.debug(SAML_DIR)
saml_logger.debug(os.listdir(SAML_DIR))
saml_logger.debug(os.listdir(os.path.join(SAML_DIR, "certs")))
saml_settings = OneLogin_Saml2_Settings(
    settings=None, custom_base_path=SAML_DIR, sp_validation_only=True
)


saml_keyFile = os.path.join(SAML_DIR, "certs", "sp.key")
private_key = xmlsec.Key.from_file(saml_keyFile, xmlsec.constants.KeyDataFormatPem)
manager = xmlsec.KeysManager()
manager.add_key(private_key)
enc_ctx = xmlsec.EncryptionContext(manager)


def decrypt_name_id(encrypted_name_id: str):
    return enc_ctx.decrypt(encrypted_name_id)


class SAMLAuthenticator(BackendAuthenticator):
    def __init__(self):
        pass

    async def login(
        self,
        request: Request,
        create_session: Callable[[Dict], Awaitable],
    ) -> Response:
        """
        Login endpoint
        """
        req = await prepare_from_fastapi_request(request)
        auth = OneLogin_Saml2_Auth(req, saml_settings)
        callback_url = auth.login()
        return RedirectResponse(url=callback_url), None

    async def login_callback(
        self,
        request: Request,
        create_session: Callable[[SessionAuthData], Awaitable],
    ):
        """
        General callback endpoint
        """
        saml_logger.debug("SAML Auth requested")
        req = await prepare_from_fastapi_request(request)
        auth = OneLogin_Saml2_Auth(req, saml_settings)
        auth.process_response()  # Process IdP response
        errors = auth.get_errors()  # This method receives an array with the errors
        saml_logger.debug("SAML processed")
        if len(errors) == 0:
            if not auth.is_authenticated():
                # This check if the response was ok and the user data retrieved or not (user authenticated)
                return "User Not authenticated"
            else:
                additional_session_data = {}
                additional_session_data["samlUserdata"] = auth.get_attributes()
                saml_logger.debug(additional_session_data["samlUserdata"])
                # This needs to be updated depending on the SAML attributes and what access restrictions
                # Should be placed. At some point this might become a configuration option or more some
                # more complex authorization scheme.
                # Now, we check, whether the user is an employee, and thus eligible to use the service
                # Log any login attempts
                additional_session_data["samlNameId"] = auth.get_nameid()
                additional_session_data["samlNameIdFormat"] = auth.get_nameid_format()
                additional_session_data["samlNameIdNameQualifier"] = (
                    auth.get_nameid_nq()
                )
                additional_session_data["samlNameIdSPNameQualifier"] = (
                    auth.get_nameid_spnq()
                )
                additional_session_data["samlSessionIndex"] = auth.get_session_index()
                try:
                    auth_groups = additional_session_data["samlUserdata"][
                        "urn:oid:1.3.6.1.4.1.5923.1.1.1.1"
                    ]
                    auth_name = additional_session_data["samlUserdata"][
                        "urn:oid:1.3.6.1.4.1.5923.1.1.1.6"
                    ][0]
                    try:
                        first_name = " ".join(
                            additional_session_data["samlUserdata"]["urn:oid:2.5.4.42"]
                        )
                        last_name = " ".join(
                            additional_session_data["samlUserdata"]["urn:oid:2.5.4.4"]
                        )
                    except:
                        # TODO: Better handling of this
                        first_name = auth_name
                        last_name = "?"
                    email = additional_session_data["samlUserdata"][
                        "urn:oid:0.9.2342.19200300.100.1.3"
                    ][0]
                except KeyError as e:
                    saml_logger.error("Necessary Attributes not found")
                    saml_logger.error(e)
                    saml_logger.error(additional_session_data["samlUserdata"])
                    raise HTTPException(
                        403, "User does not have the necessary attributes"
                    )
                saml_logger.debug(additional_session_data)
                session_data = SessionAuthData(
                    auth_id=email,
                    first_name=first_name,
                    last_name=last_name,
                    roles=auth_groups,
                    additional_data=additional_session_data,
                )

                session = await create_session(session_data)
                saml_logger.debug("Session key created, adding to request session")
                # This potentially needs to be updated to a more complex redirect scheme,
                # we might need to take the information from the session data and redirect
                return session
        else:
            saml_logger.error(
                "Error when processing SAML Response: %s %s"
                % (", ".join(errors), auth.get_last_error_reason())
            )
            raise HTTPException(403, "Error in callback")

    async def metadata(self):
        metadata = saml_settings.get_sp_metadata()
        return Response(content=metadata, media_type="text/xml")

    async def logout(self, request: Request, user, delete_session_callback):
        """
        Logout endpoint
        """
        req = await prepare_from_fastapi_request(request)
        auth = OneLogin_Saml2_Auth(req, saml_settings)
        name_id = session_index = name_id_format = name_id_nq = name_id_spnq = None
        user_data = user.userdata
        if "samlNameId" in user_data:
            name_id = user_data["samlNameId"]
        if "samlSessionIndex" in user_data:
            session_index = user_data["samlSessionIndex"]
        if "samlNameIdFormat" in user_data:
            name_id_format = user_data["samlNameIdFormat"]
        if "samlNameIdNameQualifier" in user_data:
            name_id_nq = user_data["samlNameIdNameQualifier"]
        if "samlNameIdSPNameQualifier" in user_data:
            name_id_spnq = user_data["samlNameIdSPNameQualifier"]
        url = auth.logout(
            name_id=name_id,
            session_index=session_index,
            nq=name_id_nq,
            name_id_format=name_id_format,
            spnq=name_id_spnq,
        )
        saml_logger.debug(f"Redirecting to {url}")
        request.session["LogoutRequestID"] = auth.get_last_request_id()
        return RedirectResponse(url=url)

    async def logout_callback(
        self, request: Request, user, delete_session_callback: Callable[[], Awaitable]
    ):
        """
        Single logout callback endpoint
        """
        req = await prepare_from_fastapi_request(request)
        auth = OneLogin_Saml2_Auth(req, saml_settings)
        saml_logger.debug(req)
        request_id = None
        if "LogoutRequestID" in request.session:
            request_id = request.session["LogoutRequestID"]
        saml_logger.debug(request_id)
        url = auth.process_slo(
            request_id=request_id, delete_session_cb=delete_session_callback
        )
        saml_logger.debug(url)
        errors = auth.get_errors()
        if len(errors) == 0:
            saml_logger.debug("Redirecting")
            if url is not None:
                saml_logger.debug("Redirecting to indicated url")
                # To avoid 'Open Redirect' attacks, before execute the redirection confirm
                # the value of the url is a trusted URL.
                return RedirectResponse(url, status_code=303)
            else:
                saml_logger.debug("Redirecting to default")
                # Return back to main page
                return RedirectResponse(url="/")
        elif auth.get_settings().is_debug_active():
            saml_logger.error("Got an error")
            saml_logger.error(errors)
            error_reason = auth.get_last_error_reason()
            saml_logger.error(error_reason)
            saml_logger.error(auth._last_response)
            # We will clean/i.e. logout the session anyways.
            return RedirectResponse(url="/", status_code=303)
        else:
            # We will clean/i.e. logout the session anyways.
            saml_logger.error(auth.get_last_error_reason())
            return RedirectResponse(url="/", status_code=303)


async def prepare_from_fastapi_request(request: Request):
    """
    Prepare and extract relevant information from a FastAPI Request object.

    Parameters:
    - request (Request): The FastAPI Request object representing the incoming request.

    Returns:
    - dict: A dictionary containing extracted information from the request, including:
        - "http_host": Hostname from the request URL.
        - "server_port": Port from the request URL.
        - "script_name": Path from the request URL.
        - "post_data": A dictionary containing any relevant data from the request's form data.
        - "get_data": A dictionary containing query parameters from the request URL.
        - "query_string": The raw query string from the request URL.

    Note:
    - This function is designed for processing FastAPI Request objects.
    - If "SAMLResponse" or "RelayState" is present in the form data, they are included in the "post_data" dictionary.
    - If debug is set to True, additional advanced request options may be included in the result.
    """
    rv = {
        "http_host": request.url.hostname,
        "server_port": request.url.port,
        "script_name": request.url.path,
        # Need to find the correct way to do this...
        "post_data": {},
        "get_data": dict(request.query_params),
        # Advanced request options
        # "https": "",  # Uncomment if you are running a server using https!
        # "request_uri": "",
        "query_string": request.url.query,
        # "validate_signature_from_qs": False,
        # "lowercase_urlencoding": False
    }
    # On debug, this is 0
    # saml_logger.debug(os.environ.get("GATEWAY_DEBUG", 0))
    # if not int(os.environ.get("GATEWAY_DEBUG", 0)) == 1:
    rv["https"] = "on"
    form_data = await request.form()
    if "SAMLResponse" in form_data:
        SAMLResponse = form_data["SAMLResponse"]
        rv["post_data"]["SAMLResponse"] = SAMLResponse
    if "RelayState" in form_data:
        RelayState = form_data["RelayState"]
        rv["post_data"]["RelayState"] = RelayState

    return rv

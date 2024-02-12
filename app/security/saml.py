from fastapi import Request, HTTPException, status
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from starlette.requests import HTTPConnection
import xmlsec
import logging
import os


saml_logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SAML_DIR = os.path.join(BASE_DIR, "saml", "saml_data")
saml_logger.info(SAML_DIR)
saml_logger.info(os.listdir(SAML_DIR))
saml_logger.info(os.listdir(os.path.join(SAML_DIR, "certs")))
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


def get_authed_user(conn: HTTPConnection):
    """
    Get the authenticated user from the given HTTPConnection.

    Parameters:
    - conn (HTTPConnection): The HTTPConnection object representing the current connection.

    Raises:
    - HTTPException: If no user is authenticated, a 403 Forbidden status is raised with the detail "No user authenticated".

    Returns:
    - User: The authenticated user object retrieved from the connection.
    """
    if not conn.user.is_authenticated:
        credentials_exception = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No user authenticated",
        )
        raise credentials_exception
    return conn.user


async def prepare_from_fastapi_request(request: Request, debug=False):
    """
    Prepare and extract relevant information from a FastAPI Request object.

    Parameters:
    - request (Request): The FastAPI Request object representing the incoming request.
    - debug (bool, optional): If True, additional debug information may be included in the result. Default is False.

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
        "https": "",  # Uncomment if you are running a server using https!
        # "request_uri": "",
        "query_string": request.url.query,
        # "validate_signature_from_qs": False,
        # "lowercase_urlencoding": False
    }
    form_data = await request.form()
    if "SAMLResponse" in form_data:
        SAMLResponse = form_data["SAMLResponse"]
        rv["post_data"]["SAMLResponse"] = SAMLResponse
    if "RelayState" in form_data:
        RelayState = form_data["RelayState"]
        rv["post_data"]["RelayState"] = RelayState

    return rv

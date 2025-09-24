from typing import Annotated
from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from app.security.auth import BackendUser
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.schemas.usage_schema import RequestSource
import logging
import re
import os
from app.config.agreement import check_agreement_version

admin_key_header = APIKeyHeader(name="AdminKey", auto_error=False)
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

uvlogger = logging.getLogger("app")


async def get_user_for_api_key(
    key_service: Annotated[KeyService, Depends(KeyService)],
    user_service: Annotated[UserService, Depends(UserService)],
    api_key: str = Security(api_key_header),
) -> BackendUser | None:
    """
    Retrieves and validates the API key from the header.

    Args:
    - api_key_header (str): Header containing the API key preceded by 'Bearer '.

    Returns:
    - str: The validated API key (without 'Bearer' prefix) if it passes the validation check.

    Raises:
    - HTTPException: If the provided API key is invalid or missing, it raises a 401 status code error
        with the detail "Invalid or missing API Key". Additionally, logs information about the header and key.
    """
    print("Checking API key")
    if api_key is None or api_key == "":
        return None
    api_key = re.sub("^Bearer ", "", api_key)
    print(f"API Key is: {api_key}")
    if api_key == "":
        # This should happen, if there is no API key set.
        return None
    key = await key_service.get_user_key_if_active(api_key)
    if key is not None:
        if key.user_id is not None:
            user = await user_service.get_user_by_id(key.user_id)
            assert user is not None
            return BackendUser(
                username=user.id,
                isadmin=user.admin,
                request_source=RequestSource(user_id=user.id, key=api_key),
                agreement_ok=check_agreement_version(user.accepted_agreement_version),
            )
        else:
            # This is a service. Service level we always assume that agreement is accepted.
            assert key.service is not None
            return BackendUser(
                username=key.service,
                isadmin=False,
                request_source=RequestSource(key=api_key),
                agreement_ok=True,
            )
    else:
        uvlogger.warning(f"Attempted usage with invalid key: {api_key}")
    print("Key could not be verified")
    raise HTTPException(
        status_code=401,
        detail="Invalid API Key",
    )


def get_admin_user_from_key(
    admin_key_header: str = Security(admin_key_header),
) -> BackendUser | None:
    """
    Retrieves the admin key from the header for privileged access.

    Args:
    - admin_key_header (str): Header containing the admin key.

    Returns:
    - str: The admin key if it matches the value stored in the environment variable.

    Raises:
    - HTTPException: If the provided admin key doesn't match the one stored in the environment.
        It raises a 401 status code error with the detail "Privileged Access required".
    """
    if admin_key_header is None or admin_key_header == "":
        # This should happen, if there is no API key set.
        return None
    if admin_key_header == os.environ.get("ADMIN_KEY"):
        return BackendUser(
            username="Admin",
            request_source=RequestSource(key=admin_key_header),
            isadmin=True,
            agreement_ok=True,
        )
    else:
        uvlogger.warning(f"Attempted Admin access with invalid key: {admin_key_header}")
    raise HTTPException(
        status_code=401,
        detail="Invalid API Key",
    )

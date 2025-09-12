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


admin_key_header = APIKeyHeader(name="AdminKey", auto_error=False)
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

uvlogger = logging.getLogger("app")


async def get_user_for_api_key(
    key_service: Annotated[KeyService, Depends(KeyService)],
    user_service: Annotated[UserService, Depends(UserService)],
    api_key: str = Security(api_key_header),
) -> BackendUser:
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
    api_key = re.sub("^Bearer ", "", api_key)
    if api_key == "":
        # This should happen, if there is no API key set.
        return None
    key = await key_service.get_user_key_if_active(api_key)
    if key is not None:
        if key.user is not None:
            user = await user_service.get_user_by_id(key.user)
            return BackendUser(
                username=user.id,
                isadmin=user.admin,
                request_source=RequestSource(user=user.id, key=api_key),
            )
        else:
            return BackendUser(
                username=key.service,
                isadmin=False,
                request_source=RequestSource(key=api_key),
            )
    else:
        uvlogger.warning(f"Attempted usage with invalid key: {api_key}")
    raise HTTPException(
        status_code=401,
        detail="Invalid API Key",
    )


def get_admin_user(
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
    if admin_key_header == "":
        # This should happen, if there is no API key set.
        return None
    if admin_key_header == os.environ.get("ADMIN_KEY"):
        return BackendUser(username="Admin", isadmin=True)
    else:
        uvlogger.warning(f"Attempted Admin access with invalid key: {admin_key_header}")
    raise HTTPException(
        status_code=401,
        detail="Invalid API Key",
    )

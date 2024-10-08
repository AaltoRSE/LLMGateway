from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from utils.handlers import key_handler

import logging
import re
import os


admin_key_header = APIKeyHeader(name="AdminKey")
api_key_header = APIKeyHeader(name="Authorization")

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
uvlogger = logging.getLogger("app")


def get_api_key(api_key: str = Security(api_key_header)) -> str:
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
    if key_handler.check_key(api_key):
        return api_key
    else:
        uvlogger.warn(f"Attempted usage with invalid key: {api_key}")
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API Key",
    )


def get_admin_key(admin_key_header: str = Security(admin_key_header)) -> str:
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
    if admin_key_header == os.environ.get("ADMIN_KEY"):
        return admin_key_header
    raise HTTPException(
        status_code=401,
        detail="Priviledged Access required",
    )

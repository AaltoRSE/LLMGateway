from fastapi.security import APIKeyHeader
from fastapi import Security, HTTPException

import logging
import re
import os


api_key_header = APIKeyHeader(name="Authorization")
admin_key_header = APIKeyHeader(name="AdminKey")


class SecurtyHandler:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def get_admin_key(self, admin_key_header: str = Security(admin_key_header)) -> str:
        if admin_key_header == os.environ.get("ADMIN_KEY"):
            return admin_key_header
        raise HTTPException(
            status_code=401,
            detail="Priviledged Access required",
        )

    # Need to figure out how to offer two alternative authentication methods...
    def get_api_key(
        self, key_handler, api_key_header: str = Security(api_key_header)
    ) -> str:
        api_key = re.sub("^Bearer ", "", api_key_header)
        if key_handler.check_key(api_key):
            return api_key
        else:
            self.logger.info(api_key_header)
            self.logger.info(api_key)
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key",
        )

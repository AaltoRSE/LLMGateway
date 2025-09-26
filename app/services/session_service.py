"""
This is code for a session handling interface using redis for storage.
"""

from typing import Annotated
import json
import secrets
import string
import logging

import redis.asyncio as redis
from fastapi import Depends
from app.dbs.redis.redis import get_session_client
from app.config.agreement import check_agreement_version
from app.services.user_service import UserService, User
from app.schemas.session_schema import HTTPSession
from app.schemas.user_schema import SessionAuthData

logger = logging.getLogger("app")


class SessionService:
    """
    Service for session related things and interaction with redis
    """

    def __init__(
        self,
        session_client: Annotated[redis.StrictRedis, Depends(get_session_client)],
    ):
        """
        Constructor
        """
        self.session_client = session_client
        self.expire_time = 600

    def set_session_expiration_time(self, time: int) -> None:
        """
        Set the expiration time of sessions
        """
        self.expire_time = time

    async def create_session(
        self,
        session_data: SessionAuthData,
        source_ip: str,
        user_service: UserService,
        session_key: str | None = None,
    ) -> HTTPSession:
        """
        Create a new session or update an existing session in Redis.

        Args:
            session_data (dict): A dictionary of information on the session.
                                 Must contain the following fields:
                - auth_name (str): The name of the authentication provider.
                - first_name (str): The user's first name.
                - last_name (str): The user's last name.
                - groups (list): A list of the user's roles.

            sourceIP (str): The IP address of the user.
            session_key (str, optional): The session key. If None, a new key
                                         is generated. Defaults to None.
        Returns:
            str: The session key.
        """
        print(session_data)
        if session_key is None:
            # Should be the case in most instances.
            session_key = self.generate_session_key()
            # Make sure, it doesn't exist
            exists = await self.session_client.exists(session_key)
            while exists:
                session_key = self.generate_session_key()
                exists = await self.session_client.exists(session_key)

        user: User = await user_service.get_or_create_user_from_auth_data(session_data)
        session = HTTPSession(
            key=session_key,
            ip=source_ip,
            data=session_data,
            user_id=user.id,
            auth_id=user.auth_id,
            roles=session_data.roles,
            admin=user.admin,
            quota=user.quota,
            agreement_ok=check_agreement_version(user.accepted_agreement_version),
        )
        await self.session_client.setex(
            session_key, self.expire_time, json.dumps(session.model_dump())
        )
        return session

    async def get_session(self, session_key: str) -> HTTPSession | None:
        """
        Retrieve session data from Redis.

        Args:
            session_key (str): The session key.

        Returns:
            dict: The session data, or None if the session does not exist.
        """

        serialized_data = await self.session_client.get(session_key)
        logger.debug("Session data: %s", serialized_data)
        if serialized_data is None:
            return None
        # Deserialize the JSON string back to a dictionary
        session = HTTPSession.model_validate(json.loads(serialized_data))

        # TODO: Do we refresh the session here, or should this be handled elsewhere?
        return session

    def generate_session_key(self, length: int = 128) -> str:
        """
        Function to generate an API key.

        Parameters:
        - length (int, optional): Length of the generated API key. Defaults to 64.

        Returns:
        - str: The generated API key.
        """
        alphabet = string.ascii_letters + string.digits
        api_key = "".join(secrets.choice(alphabet) for _ in range(length))
        return api_key

    async def delete_sessions_for_user(self, user_id: str) -> None:
        """
        Delete all sessions for a given user.
        NOTE: This is a quite expensive operation, but shouldn't happen too often.
        The major use case would be a quota change that should take effect immediately
        """
        keys_to_delete = []
        async for key in self.session_client.scan_iter("*"):
            value = await self.session_client.get(key)
            session_data = HTTPSession.model_validate(json.loads(value))
            if session_data.user_id == user_id:
                keys_to_delete.append(key)

        await self.session_client.delete(*keys_to_delete)

    async def delete_session(self, session_key: str) -> None:
        """
        Delete a session from Redis.

        Args:
            session_key (str): The session key.
        """
        await self.session_client.delete(session_key)

    async def update_session_agreement(
        self, session: HTTPSession, agreement_version: str
    ) -> None:
        """
        Update the user agreement setting in a given session.
        """
        session.agreement_ok = check_agreement_version(agreement_version)
        serialized_data = await self.session_client.get(session.key)
        if serialized_data is None:
            raise ValueError("Session does not exist")
        await self.session_client.setex(
            session.key, self.expire_time, json.dumps(session.model_dump())
        )

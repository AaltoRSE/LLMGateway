# This is code for a session handling interface using redis for storage.

import redis.asyncio import redis
import json
import secrets
import string
from app.dbs.redis.redis import get_session_client
from app.services.user_service import UserService, User
from app.models.session import HTTPSession
import gateway.app.dbs.redis.redis as redis_db
import logging
import os

logger = logging.getLogger("app")


class SessionService:
    def __init__(self, exp_time: int = 12 * 3600):  # 12 hours
        self.expire_time = exp_time

    async def create_session(
        self,
        session_data: dict,
        source_ip: str,
        user_service: UserService,
        session_key: str = None,
    ) -> HTTPSession:
        """
        Create a new session or update an existing session in Redis.

        Args:
            session_data (dict): A dictionary of information on the session. Must contain the following fields:
                - auth_name (str): The name of the authentication provider.
                - first_name (str): The user's first name.
                - last_name (str): The user's last name.
                - groups (list): A list of the user's roles.
                - email (str): The user's email address.

            sourceIP (str): The IP address of the user.
            session_key (str, optional): The session key. If None, a new key is generated. Defaults to None.
        Returns:
            str: The session key.
        """
        async with get_session_client() as redis_generator:
            redis_client : redis.StrictRedis = next(redis_generator)
            if session_key == None:
                # Should be the case in most instances.
                session_key = self.generate_session_key()
                # Make sure, it doesn't exist
                exists = await redis_client.exists(session_key)                
                while exists:
                    session_key = self.generate_session_key()
                    exists = await redis_client.exists(session_key)

            user : User = await user_service.get_or_create_user_from_auth_data(
                session_data["auth_name"],
                session_data["first_nq  ame"],
                session_data["last_name"],
                session_data["email"],
                session_data["auth_groups"]
            )
            session = HTTPSession(
                key=session_key,
                ip=source_ip,
                data=session_data,
                user=user.auth_id,
                roles=session_data["auth_groups"],
                admin=user.admin,
                agreement_ok=self.check_agreement_version(user.acc),
            )
            await redis_client.setex(
                session_key, self.expire_time, json.dumps(session.model_dump())
            )
        return session

    async def get_session(self, session_key: str) -> HTTPSession:
        """
        Retrieve session data from Redis.

        Args:
            session_key (str): The session key.

        Returns:
            dict: The session data, or None if the session does not exist.
        """
        async with get_session_client() as redis_generator:
            redis_client : redis.StrictRedis = next(redis_generator)
            serialized_data = await redis_client.get(session_key)
            logger.debug(f"Session data: {serialized_data}")
            if serialized_data is None:
                return None
            # Deserialize the JSON string back to a dictionary
            session = HTTPSession.model_validate(json.loads(serialized_data))

        # TODO: Do we refresh the session here, or should this be handled elsewhere?
        return session

    def generate_session_key(self, length: int = 128):
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

    async def delete_session(self, session_key: str):
        """
        Delete a session from Redis.

        Args:
            session_key (str): The session key.
        """
        async with get_session_client() as redis_generator:
            redis_client : redis.StrictRedis = next(redis_generator)
            await redis_client.delete(session_key)
        

    def check_agreement_version(self, agreement_version: str):
        return agreement_version == os.environ.get("AGREEMENT_VERSION", "1.0")

    async def update_session_agreement(self, session: HTTPSession, agreement_version: str):
        async with get_session_client() as redis_generator:
            redis_client : redis.StrictRedis = next(redis_generator)
            session.agreement_ok = self.check_agreement_version(agreement_version)
            serialized_data = await redis_client.get(session.key)
            if serialized_data is None:
                raise ValueError("Session does not exist")
            session.data["agreement_ok"] = session.agreement_ok
            await redis_client.setex(
                session.key, self.expire_time, json.dumps(session.model_dump())
            )

# This is code for a session handling interface using redis for storage.

from redis import Redis
import json
import secrets
import string
from app.services.user_service import UserService
from app.models.session import HTTPSession
import app.db.redis as redis_db


class SessionService:
    def __init__(self, exp_time: int = 12 * 3600):  # 12 hours
        self.expire_time = exp_time
        self.redis_client: Redis = redis_db.redis_session_client

    def create_session(
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

            sourceIP (str): The IP address of the user.
            session_key (str, optional): The session key. If None, a new key is generated. Defaults to None.
        Returns:
            str: The session key.
        """
        if session_key == None:
            # Should be the case in most instances.
            session_key = self.generate_session_key()
            # Make sure, it doesn't exist
            while self.redis_client.exists(session_key):
                session_key = self.generate_session_key()
        # TODO: Check the Groups are acceptable.

        user = user_service.get_or_create_user_from_auth_data(
            session_data["auth_name"],
            session_data["first_name"],
            session_data["last_name"],
        )
        data = {
            "User": user.auth_id,
            "IP": source_ip,
            "Data": session_data,
            "Roles": session_data["auth_groups"],
            "Admin": user.admin,
        }
        self.redis_client.setex(session_key, self.expire_time, json.dumps(data))
        return HTTPSession(
            key=session_key,
            ip=data["IP"],
            data=data["Data"],
            user=data["User"],
            roles=data["Roles"],
            admin=data["Admin"],
        )

    def get_session(self, session_key: str) -> HTTPSession:
        """
        Retrieve session data from Redis.

        Args:
            session_key (str): The session key.

        Returns:
            dict: The session data, or None if the session does not exist.
        """
        serialized_data = self.redis_client.get(session_key)
        if serialized_data is None:
            return None
        # Deserialize the JSON string back to a dictionary
        data = json.loads(serialized_data)
        # TODO: Do we refresh the session here, or should this be handled elsewhere?
        return HTTPSession(
            key=session_key,
            ip=data["IP"],
            data=data["Data"],
            user=data["User"],
            roles=data["Roles"],
            admin=data["Admin"],
        )

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

    def delete_session(self, session_key: str):
        """
        Delete a session from Redis.

        Args:
            session_key (str): The session key.
        """
        self.redis_client.delete(session_key)

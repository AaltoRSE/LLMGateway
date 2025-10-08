"""Entra ID authentication module"""

from enum import Enum
import logging
import time
import threading
from typing import TYPE_CHECKING, Any, List, TypedDict, Union

import jwt
import jwt.types

from jwt.algorithms import RSAAlgorithm
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from fastapi import Request, HTTPException
import requests
from app.security.auth import BackendUser, SessionAuthData, RequestSource
from app.services.user_service import UserService
from app.schemas.user_schema import User

if TYPE_CHECKING:
    # This is necessary, as AllowedRSAKeys is only created, when TYPE_CHECK is enabled, but we need it for the type hint
    from jwt.algorithms import AllowedRSAKeys

from app.security.entra_settings.entra_jwt_settings import (
    role_map,
    tenant_id,
    audience,
    valid_scopes,
)

if TYPE_CHECKING:
    # This is necessary, as AllowedRSAKeys is only created, when TYPE_CHECK is enabled, but we need it for the type hint
    from jwt.algorithms import AllowedRSAKeys

jwt_logger = logging.getLogger(__name__)


# request timeout in seconds, when fetching key issuer and openid configuration
CALL_TIMEOUT_SECONDS = 10

# Union of public/private keypair, matches
RsaKeyType = Union[RSAPrivateKey, RSAPublicKey]


class JWKS(TypedDict):
    """JWKS return type, not exchaustive"""

    keys: List[jwt.types.JWKDict]


class OpenIDConfiguration(TypedDict):
    """OpenID configuration return type, not exchaustive"""

    jwks_uri: str


def get_openid_configuration(openid_uri: str) -> OpenIDConfiguration:
    """Retrieves OpenID configuration from an URL"""
    assert openid_uri.startswith("https://")  # SECURITY: ensure TLS

    jwt_logger.info("Retrieving openid configuration")
    openid_configuration: OpenIDConfiguration = requests.get(
        openid_uri, timeout=CALL_TIMEOUT_SECONDS
    ).json()
    assert openid_configuration.get("jwks_uri") is not None
    jwt_logger.info("OpenID configuration retrieved")

    return openid_configuration


def get_jwt_keys(jwt_keys_uri: str) -> JWKS:
    """Retrieve JWT Keys from an URI"""

    try:
        assert jwt_keys_uri.startswith("https://")  # SECURITY: ensure TLS
        jwks: JWKS = requests.get(jwt_keys_uri, timeout=CALL_TIMEOUT_SECONDS).json()
        return jwks
    except Exception as e:
        jwt_logger.error("JWT keys fetch failed: %s", e)
        raise e


def map_jwt_keys_to_rsa_algorithms(tenant_id: str, jwks: JWKS) -> dict[str, RsaKeyType]:
    """Map the JWT keys into RSA algorithms. The key issuer must match the tenant"""

    rsa_keys: dict[str, AllowedRSAKeys] = {}

    for key in jwks["keys"]:
        kid = key["kid"]

        key_issuer = key.get("issuer")
        if (
            key_issuer
            and key_issuer == f"https://login.microsoftonline.com/{tenant_id}/v2.0"
        ):
            try:
                rsa_keys[kid] = RSAAlgorithm.from_jwk(key)
            except jwt.InvalidKeyError as e:
                jwt_logger.error("JWT key %s could not be decoded: %s", kid, e)

        else:
            jwt_logger.warning(
                "JWT key contained non-tenant matched issuer: %s", key_issuer
            )

    return rsa_keys


class AuthenticationExceptionType(Enum):
    NO_UNIQUE_NAME = 1
    NO_NAME = 2
    NO_KID_IN_HEADER = 3
    NO_RSA_MATCH = 4
    UNSUPPORTED_VERSION = 5
    TENANT_ID_MISMATCH = 6
    ISSUER_MISMATCH = 7
    AUDIENCE_MISMATCH = 8
    INVALID_SCOPE = 9
    AUTHORIZATION_HEADER_MISSING = 10


class AuthenticationException(Exception):
    """An exception in the authentication process"""

    def __init__(self, ty: AuthenticationExceptionType, message: str | None = None):
        default_messages = {
            AuthenticationExceptionType.NO_UNIQUE_NAME: "No unique_name in JWT payload",
            AuthenticationExceptionType.NO_NAME: "No first_name or last_name in JWT payload",
            AuthenticationExceptionType.NO_KID_IN_HEADER: "No kid value available in JWT header",
            AuthenticationExceptionType.NO_RSA_MATCH: "Relevant RSA key not available",
            AuthenticationExceptionType.UNSUPPORTED_VERSION: "Unsupported JWT token version",
            AuthenticationExceptionType.TENANT_ID_MISMATCH: "JWT token tenant ID mismatch",
            AuthenticationExceptionType.ISSUER_MISMATCH: "JWT token issuer mismatch",
            AuthenticationExceptionType.AUDIENCE_MISMATCH: "JWT token audience mismatch",
            AuthenticationExceptionType.INVALID_SCOPE: "Invalid authentication scope",
            AuthenticationExceptionType.AUTHORIZATION_HEADER_MISSING: "Authorization header missing",
        }

        if message is None:
            message = default_messages.get(ty, "An authentication error occurred")

        super().__init__(message)
        self.ty = ty
        self.message = message


class EntraJWTAuthService:
    """Entra ID JWT authentication service

    More information about Entra ID:
        https://learn.microsoft.com/en-us/entra/identity-platform/access-tokens
    """

    def __init__(
        self,
        tenant_id: str = tenant_id,
        audience: str = audience,
        role_map: dict[str, str] = role_map,
        refresh_time_period_seconds: int = 24 * 60 * 60,  # default 24 hours
        valid_scopes: List[str] | None = valid_scopes,
        insecure_predefined_keys: None | JWKS = None,
    ):

        self.tenant_id = tenant_id
        self.audience = audience

        if valid_scopes is None:
            valid_scopes = []

        self.role_map = role_map
        self.jwks: None | JWKS = None
        self.rsa_keys: dict[str, AllowedRSAKeys] = {}
        self.refresh_time_period_seconds = refresh_time_period_seconds
        self.valid_scopes = valid_scopes
        self.openid_configuration: OpenIDConfiguration | None = None

        # Construct the openid configuration URL
        # SECURITY: Ensure TLS, never switch to http here, since this is the root of trust
        if insecure_predefined_keys is not None:
            self._set_jwks(insecure_predefined_keys)
            jwt_logger.warning(
                "Using INSECURE predefined keys. This should happen only in tests."
            )
        else:
            self.openid_url = f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"
            self.openid_configuration = get_openid_configuration(self.openid_url)

        # Thread for refresh
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._key_refresh_loop)

        # Now retrieve and map the signing keys, based on open id info
        self._get_and_map_keys()

        jwt_logger.info("Keys loaded")

    def _set_jwks(self, jwks: JWKS) -> None:
        self.jwks = jwks
        self.rsa_keys = map_jwt_keys_to_rsa_algorithms(self.tenant_id, self.jwks)

    def _get_and_map_keys(self) -> None:
        if self.openid_configuration is not None:
            jwks = get_jwt_keys(self.openid_configuration["jwks_uri"])
            self._set_jwks(jwks)

    def start(self) -> None:
        jwt_logger.info("Starting key refresh thread")
        self._stop_event.clear()
        self._thread.start()

    def stop(self) -> None:
        jwt_logger.info("Stopping key refresh thread")
        self._stop_event.set()
        self._thread.join()

    def _key_refresh_loop(self) -> None:
        """The JWT key refresh thread"""
        check_interval = 1
        total_sleep = 0
        while not self._stop_event.is_set():
            if total_sleep >= self.refresh_time_period_seconds:
                jwt_logger.info("Refreshing JWT signing keys")
                try:
                    self._get_and_map_keys()
                except Exception as e:
                    jwt_logger.error("JWT key refresh failed: %s", e)
                total_sleep = 0  # Reset sleep timer after refresh
            else:
                time.sleep(check_interval)
                total_sleep += check_interval

        jwt_logger.info("Key refresh thread stopped")

    async def verify_authorization(
        self, token: str, user_service: UserService, correlation_id: str
    ) -> BackendUser | None:
        """Authorization and authentication logic for Aalto AI"""

        try:
            # Extract token
            current_user = await self._verify_token(token, user_service)
            return current_user

        except AuthenticationException as error:
            if error.ty != AuthenticationExceptionType.AUTHORIZATION_HEADER_MISSING:
                jwt_logger.error(
                    "correlation_id=%s - error during token validation: %s",
                    correlation_id,
                    error,
                )
            # None indicates, the key failed.
            return None
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            jwt.DecodeError,
            jwt.InvalidSignatureError,
            ValueError,
        ) as error:
            jwt_logger.error(
                "correlation_id=%s - error during authentication: %s",
                correlation_id,
                error,
            )
            return None

    async def _verify_token(self, token: str, user_service: UserService) -> BackendUser:
        # Validate the JWT token, and return the payload
        payload = self._validate_and_decode_jwt_token(token)

        # Map the payload into Aalto AI authenticated user, create if not exists
        current_user = await self._validate_authenticated_user(
            payload, token, user_service
        )

        return current_user

    async def _validate_authenticated_user(
        self, payload: dict[str, Any], token: str, user_service: UserService
    ) -> BackendUser:
        """Return the backend user for a decoded JWT payload"""

        groups = payload.get("groups", [])
        first_name: str | None = payload.get("given_name")
        last_name: str | None = payload.get("family_name")
        unique_name: str | None = payload.get("unique_name")

        if not unique_name or unique_name == "":
            raise AuthenticationException(AuthenticationExceptionType.NO_UNIQUE_NAME)

        if not first_name or first_name == "" or not last_name or last_name == "":
            raise AuthenticationException(AuthenticationExceptionType.NO_NAME)

        # Map entra id groups to roles
        roles = self._map_entra_group_ids_into_user_roles(groups)

        # Construct DB user either by creating a new user or fetching existing one
        user: User = await user_service.get_or_create_user_from_auth_data(
            SessionAuthData(
                auth_id=unique_name,  # Here we need to check for the auth ID
                first_name=first_name,
                last_name=last_name,
                roles=roles,
            )
        )
        if user is None:
            return None

        # Construct a backend user from the user data
        current_user = BackendUser(
            roles=roles,
            username=user.auth_id,
            request_source=RequestSource(user_id=user.id),
            isadmin=user.admin,
            agreement_ok=True,
        )

        return current_user

    def _map_entra_group_ids_into_user_roles(self, groups: list[str]) -> list[str]:
        """Map the Entra ID groups into user roles

        Fail silenty on unknown mapped roles. This is probable case to happen, when we add more roles
        """
        mapped_roles: list[str] = []

        for group in groups:
            if group in self.role_map:
                role = self.role_map[group]
                if role not in mapped_roles:
                    mapped_roles.append(role)

        return mapped_roles

    def _validate_and_decode_jwt_token(self, token: str) -> dict[str, Any]:
        """Validate the user JWT token and return JWT token decoded payload

        This is the most important security function of this method. It validates the user access
        """

        # Get the JWT header
        # Note: The signature is not verified so the header parameters should not be fully trusted until signature verification is complete
        unverified_header = jwt.get_unverified_header(token)

        # Get the specific RSA key
        # FIXME: is it ok to allow the key define kid? What kid's do we trust?
        kid: str | None = unverified_header.get("kid")
        if not kid:
            raise AuthenticationException(AuthenticationExceptionType.NO_KID_IN_HEADER)

        # Match the key from signing keys
        rsa_key = self.rsa_keys.get(kid)

        # If no key matched
        if rsa_key is None or isinstance(rsa_key, RSAPrivateKey):
            # FIXME ATF-538 add logging, if this is triggered there's something odd happening, need to log
            raise AuthenticationException(AuthenticationExceptionType.NO_RSA_MATCH)

        expected_issuer = f"https://sts.windows.net/{self.tenant_id}/"

        # Verify the jwt token signature and return the token claims.
        # See: https://pyjwt.readthedocs.io/en/stable/api.html#jwt.decode
        payload = jwt.decode(
            token,  # the token to be decoded
            rsa_key,  # the key suitable for allowed algorithm
            audience=self.audience,  # the value for verify_aud check
            issuer=expected_issuer,  # the value for verify_iss check
            algorithms=["RS256"],
            # FIXME: leeway check by default 0, do we need it?
            options={
                "verify_signature": True,  # IMPORTANT - MUST BE ALWAYS TRUE: verify the JWT cryptographic signature
                "require": [
                    "scp",
                    "iss",
                ],  # list of claims that must be present  - DOES NOT VERIFY VALIDITY!
            },
        )

        # Ensure token version is as expected
        token_version = payload.get("ver")
        if token_version not in ["1.0", "2.0"]:
            raise AuthenticationException(
                AuthenticationExceptionType.UNSUPPORTED_VERSION,
                f"Unsupported JWT token version {token_version}",
            )

        # Ensure that token is produced by valid tenant id
        tenant_id_in_token = payload.get("tid")
        if tenant_id_in_token != self.tenant_id:
            raise AuthenticationException(
                AuthenticationExceptionType.TENANT_ID_MISMATCH,
                f"JWT token tenant ID mismatch ({tenant_id_in_token} != {self.tenant_id})",
            )

        ##### Double checks below - jwt.decode matches these but for redundancy

        # Ensure issuer
        if payload.get("iss") != expected_issuer:
            raise AuthenticationException(AuthenticationExceptionType.ISSUER_MISMATCH)

        # Ensure audience
        if payload.get("aud") != self.audience:
            raise AuthenticationException(AuthenticationExceptionType.AUDIENCE_MISMATCH)

        # Ensure that the scp parameters is to this service
        if payload.get("scp") not in self.valid_scopes:
            raise AuthenticationException(AuthenticationExceptionType.INVALID_SCOPE)

        return payload


# Singleton instance
auth_service_instance: EntraJWTAuthService | None = None


# Retrieve authentication service singleton instance
def get_entrajwt_auth_service() -> EntraJWTAuthService:
    global auth_service_instance  # pylint: disable=global-variable-not-assigned
    assert auth_service_instance is not None
    return auth_service_instance


# Initialize authentication service singleton
def build_global_service() -> None:
    global auth_service_instance  # pylint: disable=global-statement
    service = EntraJWTAuthService()
    assert auth_service_instance is None
    auth_service_instance = service

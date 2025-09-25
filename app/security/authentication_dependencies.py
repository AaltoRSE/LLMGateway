import logging

from starlette.requests import HTTPConnection
from starlette.authentication import AuthCredentials
from fastapi import HTTPException, Depends

logger = logging.getLogger("app")

from app.security.auth import BackendUser
from app.security.api_keys import get_user_for_api_key, get_admin_user_from_key
from app.security.session import get_user_from_session


async def authenticate_request(
    conn: HTTPConnection,
    session_user: BackendUser = Depends(get_user_from_session),
    api_key_user: BackendUser = Depends(get_user_for_api_key),
    admin_user: BackendUser = Depends(get_admin_user_from_key),
) -> BackendUser | None:
    user = None
    if session_user is not None:
        user = session_user
    # We allow combining a key and a session request.
    if user is not None:
        if api_key_user is not None:
            user.request_source.key = api_key_user.request_source.key
    elif api_key_user is not None:
        user = api_key_user
    # Mixing sessions and admin API keys is not allowed, admin key will be ignored in this case.
    if user is None and admin_user is not None:
        user = admin_user
    logger.info(conn)
    if user is not None:
        logger.info("setting user for scope")
        # Potentially the credentials can be improved...
        conn.scope["auth"], conn.scope["user"] = (
            AuthCredentials(["authenticated"]),
            user,
        )
        return user
    else:
        logger.info("Setting user")
        conn.scope["auth"], conn.scope["user"] = (None, None)
        return None


async def requires_auth(
    user: BackendUser | None = Depends(authenticate_request),
) -> BackendUser:
    """
    This dependency secures endpoints that necessarily require some form of authentication
    No assumption can be made about the content of the BackendUser.
    Username can e.g. be the name of a service and is NOT the same as the user_id
    """
    print("Checking authentication")
    if user is None:
        print("No user")
        raise HTTPException(401, "Unauthenticated")
    return user


async def requires_agreement(
    user: BackendUser | None = Depends(authenticate_request),
) -> BackendUser:
    """
    This dependency secures endpoints that necessarily require some form of authentication
    No assumption can be made about the content of the BackendUser.
    Username can e.g. be the name of a service and is NOT the same as the user_id
    """
    user = await requires_auth(user)
    if not user.agreement_ok:
        raise HTTPException(403, "Need to accept current agreement")
    return user


async def requires_key(user: BackendUser = Depends(requires_agreement)) -> BackendUser:
    """
    This dependency secures endpoints that necessarily require a key
    An endpoint using this dependency, can rely on user.request_source.key to be not None
    """
    if user.request_source.has_key():
        return user
    raise HTTPException(403, "Endpint requires key authentication")


async def requires_user(user: BackendUser = Depends(requires_agreement)) -> BackendUser:
    """
    This dependency secures endpoints and ensures, that a user_id is associated with
    the request, i.e. the user.request_source.user_id field is set and valid.
    """
    if user.request_source.user_id is not None:
        return user
    raise HTTPException(403, "Endpoint cannot be used with a service key")


async def requires_session(
    user: BackendUser | None = Depends(authenticate_request),
) -> BackendUser:
    """
    This dependency secures endpoints that require an active session.
    requires_session allows for a agreement that is not accepted, sinceit assumes UI interaction
    """
    if user is None:
        raise HTTPException(401, "Unauthenticated")
    if user.request_source.has_session:
        return user
    raise HTTPException(403, "Endpoint requires a valid session")


async def requires_admin(
    user: BackendUser | None = Depends(authenticate_request),
) -> BackendUser:
    """
    Using this dependency secures an endpoint ensuring, that only admin users, or a
    request with the admin key can access this endpoint.
    """
    print("Checking authentication")
    if user is None:
        print("No user")
        raise HTTPException(401, "Unauthenticated")
    if not user.is_admin():
        print("User not admin")
        raise HTTPException(403, "Unauthorized")
    return user

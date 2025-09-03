import logging

from typing import Annotated
from fastapi import Depends, Request
from starlette.authentication import AuthCredentials
# Unfortunately we need to import the whole stack here, as FastAPI dependency injection
# does not work with starlette middlewares.

from app.security.auth_types import BackendUser
from app.security.entra_jwt import EntraJWTAuthService, get_entrajwt_auth_service
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

def get_user(
    request: Request,
    user_service: Annotated[UserService, Depends(UserService)],
    auth_service: Annotated[EntraJWTAuthService, Depends(get_entrajwt_auth_service)]
) -> BackendUser:
    authenticated_user = auth_service.verify_authorization(request, user_service)

    # Set the state for authenticated user
    request.scope["user"] = authenticated_user
    request.scope["auth"] = AuthCredentials(["authenticated"])
    return authenticated_user

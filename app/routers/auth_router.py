import logging
from typing import Annotated
from fastapi import (
    APIRouter,
    Request,
    Security,
    Depends,
)

from app.security.authentication_dependencies import (
    authenticate_request,
)
from app.services.user_service import UserService, User
from app.security.auth import BackendUser
from app.responses.auth import AuthInfo, SessionAuthData

logger = logging.getLogger("app")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/test")
@router.post("/test")
async def test_authentication(
    request: Request,
    user_service: Annotated[UserService, Depends(UserService)],
    user: BackendUser = Depends(authenticate_request),
) -> AuthInfo:
    """
    Test authentication endpoint
    """
    auth_data = AuthInfo(authed=False)
    if user is not None:
        if user.request_source.user_id is not None:
            system_user: User = await user_service.get_user_by_id(
                user.request_source.user_id
            )
            auth_data.user = SessionAuthData(
                first_name=system_user.first_name,
                last_name=system_user.last_name,
                auth_id=system_user.auth_id,
                roles=user.roles,
            )
            auth_data.authed = True
            auth_data.admin = user.is_admin()
            auth_data.agreement_ok = user.agreement_ok
        else:
            auth_data.authed = True
            auth_data.admin = user.is_admin()
            auth_data.agreement_ok = user.agreement_ok
    return auth_data


@router.get("/test_admin")
async def test_admin(
    request: Request, user: BackendUser = Security(authenticate_request)
):
    """
    Test authentication endpoint
    """
    info = AuthInfo(authed=False)
    if user is not None and user.is_admin():
        info.admin = True
        info.authed = True
    return info

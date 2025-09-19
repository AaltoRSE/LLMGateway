from typing import Annotated
from fastapi import APIRouter, Request, Security, status, Depends
from app.security.authentication_dependencies import requires_admin, BackendUser
from app.requests.admin_requests import *
from app.services.user_service import UserService


import logging

router = APIRouter(prefix="/user", tags=["user"])

logger = logging.getLogger("app")


@router.post("/list_users", status_code=status.HTTP_200_OK)
def list_users(
    RequestData: Request,
    user_service: Annotated[UserService, Depends(UserService)],
    admin_key: BackendUser = Security(requires_admin),
):
    return user_service.get_all_users()

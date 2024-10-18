from app.requests.admin_requests import *
from app.requests.general_requests import UserRequest
from typing import Annotated
from fastapi import APIRouter, Request, Security, HTTPException, status, Depends
from app.security.api_keys import get_admin_key
from app.security.auth import get_admin_user, get_user, BackendUser
from app.services.model_service import ModelService
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.models.model import LLMModel, LLMModelData


import logging

router = APIRouter(prefix="/user", tags=["user"])

logger = logging.getLogger("app")


@router.post("/list_users", status_code=status.HTTP_200_OK)
def list_users(
    RequestData: Request,
    user_service: Annotated[UserService, Depends(UserService)],
    admin_key: BackendUser = Security(get_admin_user),
):
    return user_service.get_all_users()

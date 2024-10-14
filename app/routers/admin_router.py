from app.requests.admin_requests import *
from app.requests.general_requests import UserRequest
from typing import Annotated
from fastapi import APIRouter, Request, Security, HTTPException, status, Depends
from app.security.api_keys import get_admin_key
from app.security.auth import get_admin_user, BackendUser
from app.services.model_service import ModelService
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.models.model import LLMModel, LLMModelData


import logging

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Security(get_admin_key)]
)

logger = logging.getLogger("admin")


# Admin endpoints
@router.post("/addmodel", status_code=status.HTTP_201_CREATED)
def add_model(
    modelData: AddAvailableModelRequest,
    model_handler: Annotated[ModelService, Depends(ModelService)],
    admin_user: BackendUser = Depends(get_admin_user),
):
    model_to_add = LLMModel(
        path=modelData.target_path,
        prompt_cost=modelData.prompt_cost,
        completion_cost=modelData.completion_cost,
        name=modelData.name,
        description=modelData.description,
        model=LLMModelData(
            id=modelData.id,
            owned_by=modelData.owner,
            permissions=[],
        ),
    )
    try:
        model_handler.add_model(model_to_add)
    except KeyError as e:
        raise HTTPException(status.HTTP_409_CONFLICT)


@router.post("/removemodel", status_code=status.HTTP_200_OK)
def remove_model(
    RequestData: RemoveModelRequest,
    model_handler: Annotated[ModelService, Depends(ModelService)],
    admin_user: BackendUser = Depends(get_admin_user),
):
    try:
        model_handler.remove_model(RequestData.model)
    except KeyError as e:
        raise HTTPException(status.HTTP_410_GONE)


# This resets the given ser to the default status.
# This is mostly for testing purposes....
@router.post("/reset_user", status_code=status.HTTP_200_OK)
def reset_user(
    RequestData: UserRequest,
    user_service: Annotated[UserService, Depends(UserService)],
    admin_user: BackendUser = Depends(get_admin_user),
):
    user = user_service.reset_user(RequestData.username)
    if user:
        return user
    else:
        raise HTTPException(404, "User not found")


@router.get("/listkeys", status_code=status.HTTP_200_OK)
def list_keys(
    RequestData: Request,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    admin_key: str = Security(get_admin_key),
):
    logger.debug("Keys requested")
    return key_handler.list_keys()


@router.get("/list_users", status_code=status.HTTP_200_OK)
def list_users(
    RequestData: Request,
    user_service: Annotated[UserService, Depends(UserService)],
    admin_key: str = Security(get_admin_key),
):
    return user_service.get_all_users()

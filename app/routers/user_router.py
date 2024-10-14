from app.requests.admin_requests import *
from app.requests.general_requests import UserRequest
from typing import Annotated
from fastapi import APIRouter, Request, Security, HTTPException, status, Depends
from app.security.api_keys import get_admin_key
from app.security.auth import get_admin_user
from app.services.model_service import ModelService
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.models.model import LLMModel, LLMModelData


import logging

router = APIRouter(prefix="/user", tags=["user"])

logger = logging.getLogger("app")


# Admin endpoints
@router.post("/addmodel", status_code=status.HTTP_201_CREATED)
def add_model(
    modelData: AddAvailableModelRequest,
    model_handler: Annotated[ModelService, Depends(ModelService)],
    admin_key: str = Security(get_admin_key),
):
    model_to_add = LLMModel(
        path=modelData.target_path,
        prompt_cost=modelData.prompt_cost,
        completion_cost=modelData.completion_cost,
        model=LLMModelData(
            id=modelData.model,
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
    admin_key: str = Security(get_admin_key),
):
    try:
        model_handler.remove_model(RequestData.model)
    except KeyError as e:
        raise HTTPException(status.HTTP_410_GONE)


@router.post("/addapikey", status_code=status.HTTP_201_CREATED)
def add_key(
    RequestData: AddApiKeyRequest,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    admin_key: str = Security(get_admin_key),
):
    if key_handler.add_key(
        user=RequestData.user, api_key=RequestData.key, name=RequestData.name
    ):
        pass
    else:
        raise HTTPException(409, "Key already exists")


@router.post("/removeapikey", status_code=status.HTTP_200_OK)
def remove_key(
    RequestData: AddApiKeyRequest,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    admin_key: str = Security(get_admin_key),
):
    if key_handler.delete_key(key=RequestData.key):
        pass
    else:
        raise HTTPException(409, "Key already exists")


# This resets the given ser to the default status.
# This is mostly for testing purposes....
@router.post("/reset_user", status_code=status.HTTP_200_OK)
def reset_user(
    RequestData: UserRequest,
    user_service: Annotated[UserService, Depends(UserService)],
    admin_key: str = Security(get_admin_key),
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

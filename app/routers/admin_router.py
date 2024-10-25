from app.requests.admin_requests import *
from app.requests.general_requests import UserRequest
from typing import Annotated, List
from fastapi import APIRouter, Request, Security, HTTPException, status, Depends
from app.security.api_keys import get_admin_key
from app.security.auth import get_admin_user, BackendUser
from app.services.model_service import ModelService
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.services.usage_service import UsageService
from app.models.model import LLMModel, LLMModelData
from app.models.user import UserData
from app.models.quota import PerHourUsage


import logging

router = APIRouter(prefix="/admin", tags=["admin"])

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
            owned_by=admin_user.username,
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
    user = user_service.get_user_by_id(RequestData.username)
    if user:
        user_service.reset_user(user)
        return user
    else:
        raise HTTPException(404, "User not found")


@router.get("/listkeys", status_code=status.HTTP_200_OK)
def list_keys(
    RequestData: Request,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    admin_key: BackendUser = Security(get_admin_user),
):
    logger.debug("Keys requested")
    return key_handler.list_keys()


@router.post("/list_users", status_code=status.HTTP_200_OK)
def list_users(
    RequestData: Request,
    user_service: Annotated[UserService, Depends(UserService)],
    admin_key: BackendUser = Security(get_admin_user),
) -> List[UserData]:
    users = [
        UserData.model_validate(user.model_dump(exclude="keys"))
        for user in user_service.get_all_users()
    ]
    return users


@router.post("/set_admin", status_code=status.HTTP_200_OK)
def get_user_usage(
    request: SetAdminRequest,
    user_service: Annotated[UserService, Depends(UserService)],
    admin: BackendUser = Security(get_admin_user),
):
    if admin.username == request.username:
        raise HTTPException(
            status_code=400, detail="Cannot change your own admin status"
        )
    user_service.set_admin_status(request.username, request.admin)


@router.post("/get_usage_per_user", status_code=status.HTTP_200_OK)
def get_user_usage(
    RequestData: Request,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    admin_key: BackendUser = Security(get_admin_user),
):
    return usage_service.get_usage_per_user()


@router.post("/get_usage_for_user", status_code=status.HTTP_200_OK)
def get_usage_for_user(
    request: UserRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    admin_key: BackendUser = Security(get_admin_user),
) -> List[PerHourUsage]:
    return usage_service.get_usage_over_time_for_user(request.username)


@router.get("/models", status_code=status.HTTP_200_OK)
def get_details_for_model(
    model_service: Annotated[ModelService, Depends(ModelService)],
    admin_key: BackendUser = Security(get_admin_user),
) -> List[LLMModel]:
    models = model_service.get_models()
    logger.info(models)
    return models

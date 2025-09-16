from typing import Annotated, List
from fastapi import APIRouter, Request, Security, HTTPException, status, Depends

from app.requests.admin_requests import *
from app.requests.general_requests import UserRequest, UserUsageRequest
from app.security.auth import get_admin_user, BackendUser
from app.services.model_service import ModelService
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.services.usage_service import UsageService
from app.services.balance_service import BalanceService
from app.schemas.llmmodel_schema import LLMModelData, LLMModelDataDetails
from app.schemas.key_schema import APIKey
from app.models.user import UserData
from app.schemas.usage_schema import APIRequest


import logging

router = APIRouter(prefix="/admin", tags=["admin"])

logger = logging.getLogger("admin")


# Admin endpoints
@router.post("/addmodel", status_code=status.HTTP_201_CREATED)
def add_model(
    modelData: LLMModelData,
    model_handler: Annotated[ModelService, Depends(ModelService)],
    admin_user: BackendUser = Depends(get_admin_user),
):
    try:
        model_handler.add_model(modelData)
    except KeyError as e:
        raise HTTPException(status.HTTP_409_CONFLICT)


@router.post("/removemodel", status_code=status.HTTP_200_OK)
def remove_model(
    remove: RemoveModelRequest,
    model_handler: Annotated[ModelService, Depends(ModelService)],
    admin_user: BackendUser = Depends(get_admin_user),
):
    try:
        model_handler.remove_model(remove.model)
    except KeyError as e:
        raise HTTPException(status.HTTP_410_GONE)


@router.get("/models", status_code=status.HTTP_200_OK)
def get_details_for_model(
    model_service: Annotated[ModelService, Depends(ModelService)],
    admin_key: BackendUser = Security(get_admin_user),
) -> List[LLMModelData]:
    models = model_service.get_models()
    logger.debug(models)
    return models


@router.post("/update_model", status_code=status.HTTP_200_OK)
def get_details_for_model(
    modelData: AddAvailableModelRequest,
    model_service: Annotated[ModelService, Depends(ModelService)],
    admin_user: BackendUser = Security(get_admin_user),
):
    model_to_update = LLMModelData(
        path=modelData.path,
        prompt_cost=modelData.prompt_cost,
        completion_cost=modelData.completion_cost,
        name=modelData.name,
        description=modelData.description,
        model=LLMModelData(
            id=modelData.id,
            owned_by=admin_user.username,
            permissions=[],
            type=modelData.type,
        ),
    )
    model_service.update_model(model_to_update)


# This resets the given ser to the default status.
# This is mostly for testing purposes....
@router.post("/reset_user", status_code=status.HTTP_200_OK)
async def reset_user(
    RequestData: UserRequest,
    user_service: Annotated[UserService, Depends(UserService)],
    admin_user: BackendUser = Depends(get_admin_user),
) -> None:
    user = await user_service.get_user_by_id(RequestData.username)
    if user:
        await user_service.reset_user(user)
    else:
        raise HTTPException(404, "User not found")


@router.get("/listkeys")
@router.post("/listkeys")
def list_keys(
    RequestData: Request,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    admin_key: BackendUser = Security(get_admin_user),
) -> List[APIKey]:
    logger.debug("Keys requested")
    return key_handler.list_keys()


@router.post("/list_users", status_code=status.HTTP_200_OK)
async def list_users(
    RequestData: Request,
    user_service: Annotated[UserService, Depends(UserService)],
    admin_key: BackendUser = Security(get_admin_user),
) -> List[UserData]:
    users = [
        UserData.model_validate(user.model_dump(exclude="keys"))
        async for user in user_service.get_all_users()
    ]
    return users


@router.post("/set_admin", status_code=status.HTTP_200_OK)
async def set_admin(
    request: SetAdminRequest,
    user_service: Annotated[UserService, Depends(UserService)],
    admin: BackendUser = Security(get_admin_user),
):
    if admin.username == request.username:
        raise HTTPException(
            status_code=400, detail="Cannot change your own admin status"
        )
    await user_service.set_admin_status(request.username, request.admin)


@router.post("/get_usage_per_user", status_code=status.HTTP_200_OK)
async def get_user_usage(
    balance_service: Annotated[BalanceService, Depends(BalanceService)],
    admin_key: BackendUser = Security(get_admin_user),
):
    return await balance_service.get_user_balances()


@router.post("/get_usage_for_user", status_code=status.HTTP_200_OK)
def get_usage_for_user(
    request: UserUsageRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    admin_key: BackendUser = Security(get_admin_user),
) -> List[APIRequest]:
    return usage_service.get_usage_for_user(
        request.user_id, from_time=request.from_time, to_time=request.to_time
    )

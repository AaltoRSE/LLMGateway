"""
Administrative Router
"""

import logging

from typing import Annotated, List
from fastapi import APIRouter, Security, HTTPException, status, Depends

from app.requests.admin_requests import RemoveModelRequest, SetAdminRequest
from app.requests.general_requests import UserRequest, UserUsageRequest
from app.security.authentication_dependencies import requires_admin, BackendUser
from app.services.model_service import ModelService
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.services.usage_service import UsageService, Balance
from app.services.balance_service import BalanceService
from app.schemas.llmmodel_schema import LLMModelData
from app.schemas.key_schema import APIKey
from app.schemas.usage_schema import APIRequest
from app.schemas.user_schema import User


router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(requires_admin)]
)

logger = logging.getLogger("admin")


# Admin endpoints
@router.post("/addmodel", status_code=status.HTTP_201_CREATED)
async def add_model(
    model_data: LLMModelData,
    model_handler: Annotated[ModelService, Depends(ModelService)],
) -> None:
    """
    Route for adding models
    """
    print(model_data)
    await model_handler.add_model(model_data)


@router.post("/removemodel", status_code=status.HTTP_200_OK)
async def remove_model(
    remove: RemoveModelRequest,
    model_handler: Annotated[ModelService, Depends(ModelService)],
) -> None:
    """
    Route for removing models
    """
    try:
        await model_handler.remove_model(remove.model)
    except KeyError as e:
        raise HTTPException(status.HTTP_410_GONE) from e


@router.get("/models", status_code=status.HTTP_200_OK)
async def get_details_for_model(
    model_service: Annotated[ModelService, Depends(ModelService)],
) -> List[LLMModelData]:
    """
    Route to list admin models
    """
    models = await model_service.get_models()
    logger.debug(models)
    return models


@router.post("/update_model", status_code=status.HTTP_200_OK)
async def update_model(
    model_data: LLMModelData,
    model_service: Annotated[ModelService, Depends(ModelService)],
) -> None:
    """
    Route to update model data
    """
    await model_service.update_model(model_data)


# This resets the given ser to the default status.
# This is mostly for testing purposes....
@router.post("/reset_user", status_code=status.HTTP_200_OK)
async def reset_user(
    request_data: UserRequest,
    user_service: Annotated[UserService, Depends(UserService)],
) -> None:
    """
    Route to reset a user (mainly reset their Agreement setting)
    """
    user = await user_service.get_user_by_id(request_data.user_id)
    if user:
        await user_service.reset_user(user.id)
    else:
        raise HTTPException(404, "User not found")


@router.get("/listkeys")
@router.post("/listkeys")
async def list_keys(
    key_handler: Annotated[KeyService, Depends(KeyService)],
) -> List[APIKey]:
    """
    List all keys available.
    """
    logger.debug("Keys requested")
    return await key_handler.list_keys()


@router.post("/list_users", status_code=status.HTTP_200_OK)
async def list_users(
    user_service: Annotated[UserService, Depends(UserService)],
) -> List[User]:
    """
    List users
    """
    users = await user_service.get_all_users()
    return users


@router.post("/set_admin", status_code=status.HTTP_200_OK)
async def set_admin(
    request: SetAdminRequest,
    user_service: Annotated[UserService, Depends(UserService)],
    admin: BackendUser = Security(requires_admin),
) -> None:
    """
    Set the admin setting for another user
    """
    if admin.request_source.user_id == request.user_id:
        raise HTTPException(
            status_code=400, detail="Cannot change your own admin status"
        )
    await user_service.set_admin_status(request.user_id, request.admin)


@router.get("/get_balance_per_user", status_code=status.HTTP_200_OK)
async def get_user_usage(
    balance_service: Annotated[BalanceService, Depends(BalanceService)],
) -> List[Balance]:
    """
    Get the current balance of all users (this month)
    """
    return await balance_service.get_user_balances()


@router.post("/get_usage_for_user", status_code=status.HTTP_200_OK)
async def get_usage_for_user(
    request: UserUsageRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
) -> List[APIRequest]:
    """
    Get the detailed usage for a user in the provided time
    """
    return await usage_service.get_usage_for_user(
        request.user_id, from_time=request.from_time, to_time=request.to_time
    )

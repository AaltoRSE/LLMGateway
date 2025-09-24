"""
Router for self service actions
"""

from typing import Annotated, List

from fastapi import APIRouter, Security, HTTPException, status, Depends
from app.services.usage_service import UsageService, APIRequest
from app.services.key_service import KeyService, APIKey
from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.requests.self_service_requests import (
    CreateKeyRequest,
    DeleteKeyRequest,
    ObtainUsageRequest,
)
from app.security.authentication_dependencies import requires_session, BackendUser
from app.security.session import get_session
from app.schemas.session_schema import HTTPSession

from app.config import app_configuration

# This router requires a session. Other routers might be used with pure user information
# assuming e.g. a professor gives a key to a student.
router = APIRouter(
    prefix="/selfservice",
    tags=["selfservice"],
    dependencies=[Security(requires_session)],
)


@router.post("/createkey", status_code=status.HTTP_201_CREATED)
async def create_key(
    create_request: CreateKeyRequest,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    user: BackendUser = Security(requires_session),
) -> APIKey:
    """
    Route for key creation
    """
    new_key = await key_handler.create_key(
        user_id=user.request_source.user_id, name=create_request.name
    )
    if new_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum number of keys reached",
        )
    return new_key


@router.post("/deletekey")
async def delete_key(
    delete_request: DeleteKeyRequest,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    user: BackendUser = Security(requires_session),
) -> None:
    """
    Route for key deletion
    """
    if user is not None and user.request_source.user_id is not None:
        await key_handler.delete_key_for_user(
            user_id=user.request_source.user_id, key=delete_request.key
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated but no user name",
        )


@router.post("/getkeys")
async def get_keys(
    key_handler: Annotated[KeyService, Depends(KeyService)],
    user: BackendUser = Security(requires_session),
) -> List[APIKey]:
    """
    Route for users to get their key data
    """
    keys = await key_handler.list_keys(user_id=user.request_source.user_id)
    return keys


@router.post("/usage")
async def get_usage(
    request: ObtainUsageRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    user: BackendUser = Security(requires_session),
) -> List[APIRequest]:
    """
    Route to get user Usage
    """
    assert user is not None and user.request_source.user_id is not None
    usage = await usage_service.get_usage_for_user(
        user_id=user.request_source.user_id,
        from_time=request.from_time,
        to_time=request.to_time,
    )
    return usage


@router.post("/accept_agreement")
async def accept_agreement(
    user_service: Annotated[UserService, Depends(UserService)],
    session_service: Annotated[SessionService, Depends(SessionService)],
    session: HTTPSession = Depends(get_session),
    user: BackendUser = Security(requires_session),
) -> None:
    """
    Route to accept the current user agreement
    """
    assert user is not None and user.request_source.user_id is not None
    await user_service.update_agreement_version(
        user_id=user.request_source.user_id,
        version=app_configuration.current_agreement_version,
    )
    await session_service.update_session_agreement(
        session, app_configuration.current_agreement_version
    )

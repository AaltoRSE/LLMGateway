from fastapi import APIRouter, Security, Request, HTTPException, status, Depends
from typing import Annotated
from app.services.usage_service import UsageService
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.requests.self_service_requests import *
from app.security.authentication_dependencies import requires_session, BackendUser
from app.middleware.session_middleware import get_session
from app.models.session import HTTPSession
from app.responses.self_service import *


# This router requires a session. Other routers might be used with pure user information
# assuming e.g. a professor gives a key to a student.
router = APIRouter(
    prefix="/selfservice",
    tags=["selfservice"],
    dependencies=[Security(requires_session)],
)


@router.post("/createkey")
async def create_key(
    createRequest: CreateKeyRequest,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    user: BackendUser = Security(requires_session),
):
    if not user == None:
        new_key = key_handler.create_key(
            user=user.request_source.user_id, name=createRequest.name
        )
    else:
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST, detail="Authenticated but no user name"
        )
    if new_key == None:
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST, detail="Maximum number of keys reached"
        )
    return new_key


@router.post("/deletekey")
async def delete_key(
    deleteRequest: DeleteKeyRequest,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    user: BackendUser = Security(requires_session),
):
    if not user == None:
        key_handler.delete_key_for_user(
            user=user.request_source.user_id, key=deleteRequest.key
        )
    else:
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST, detail="Authenticated but no user name"
        )
    return


@router.post("/getkeys")
async def get_keys(
    request: Request,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    user: BackendUser = Security(requires_session),
):
    keys = key_handler.list_keys(user=user.request_source.user_id)
    return keys


@router.post("/usage")
async def get_usage(
    request: ObtainUsageRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    user: BackendUser = Security(requires_session),
):
    usage = usage_service.get_usage_for_user(
        user=user.request_source.user_id,
        from_time=request.from_time,
        to_time=request.to_time,
    )
    return usage


@router.post("/accept_agreement")
async def accept_agreement(
    agreement: AcceptAgreement,
    user_service: Annotated[UserService, Depends(UserService)],
    session_service: Annotated[SessionService, Depends(SessionService)],
    session: HTTPSession = Depends(get_session),
    user: BackendUser = Security(requires_session),
):
    user_service.update_agreement_version(
        user.request_source.user_id, agreement.version
    )
    session_service.update_session_agreement(session, agreement.version)

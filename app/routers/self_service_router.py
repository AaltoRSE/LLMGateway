from fastapi import APIRouter, Security, Request, HTTPException, status, Depends
from typing import Annotated
from app.services.usage_service import UsageService
from app.services.model_service import ModelService
from app.services.key_service import KeyService
from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.requests.self_service_requests import *
from app.security.auth import get_user, BackendUser
from app.middleware.session_middleware import get_session
from app.models.session import HTTPSession
from app.responses.self_service import *
import logging

router = APIRouter(
    prefix="/selfservice",
    tags=["selfservice"],
    dependencies=[Security(get_user)],
)


@router.post("/createkey")
async def create_key(
    createRequest: CreateKeyRequest,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    user: BackendUser = Security(get_user),
):
    if not user == None:
        new_key = key_handler.create_key(user=user.username, name=createRequest.name)
    else:
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST, detail="Authenticated but no user name"
        )
    if new_key == None:
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST, detail="MAximum number of keys reached"
        )
    return new_key


@router.post("/deletekey")
async def delete_key(
    deleteRequest: DeleteKeyRequest,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    user: BackendUser = Security(get_user),
):
    if not user == None:
        key_handler.delete_key_for_user(user=user.username, key=deleteRequest.key)
    else:
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST, detail="Authenticated but no user name"
        )
    return


@router.post("/getkeys")
async def get_keys(
    request: Request,
    key_handler: Annotated[KeyService, Depends(KeyService)],
    user: BackendUser = Security(get_user),
):
    keys = key_handler.list_keys(user=user.username)
    return keys


@router.post("/usage")
async def get_usage(
    request: ObtainUsageRequest,
    usage_service: Annotated[UsageService, Depends(UsageService)],
    user: BackendUser = Security(get_user),
):
    usage = usage_service.get_usage_per_key_for_user(
        user=user.username,
        from_time=request.from_time,
        to_time=request.to_time,
        only_active=True,
    )
    return usage


@router.get("/models")
async def get_models(
    request: Request,
    model_service: Annotated[ModelService, Depends(ModelService)],
    user: BackendUser = Security(get_user),
) -> ModelListResponse:
    models = model_service.get_models()

    return [
        ModelDescription(
            prompt_cost=model.prompt_cost,
            completion_cost=model.completion_cost,
            name=model.name,
            description=model.description,
            model_id=model.model.id,
        )
        for model in models
    ]


@router.post("/accept_agreement")
async def accept_agreement(
    agreement: AcceptAgreement,
    user_service: Annotated[UserService, Depends(UserService)],
    session_service: Annotated[SessionService, Depends(SessionService)],
    session: HTTPSession = Depends(get_session),
    user: BackendUser = Security(get_user),
):
    user_service.update_agreement_version(user.username, agreement.version)
    session_service.update_session_agreement(session, agreement.version)

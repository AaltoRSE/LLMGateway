from fastapi import APIRouter, Security, Request, HTTPException, status
from utils.handlers import model_handler, key_handler, logging_handler
from .self_service_requests import *
from security.saml import get_authed_user
import logging

router = APIRouter(
    prefix="/selfservice",
    tags=["selfservice"],
    dependencies=[Security(get_authed_user)],
)


@router.post("/createkey")
async def create_key(createRequest: CreateKeyRequest, user=Security(get_authed_user)):
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
async def create_key(deleteRequest: DeleteKeyRequest, user=Security(get_authed_user)):
    if not user == None:
        key_handler.delete_key_for_user(user=user.username, key=deleteRequest.key)
    else:
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST, detail="Authenticated but no user name"
        )
    return


@router.post("/getkeys")
async def get_keys(request: Request, user=Security(get_authed_user)):
    keys = key_handler.list_keys(user=user.username)
    return keys


@router.post("/usage")
async def get_usage(request: ObtainUsageRequest, user=Security(get_authed_user)):
    usage = logging_handler.get_usage_for_user(
        username=user.username,
        from_time=request.from_time,
        to_time=request.to_time,
    )
    return usage

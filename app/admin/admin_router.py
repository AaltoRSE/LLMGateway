from .admin_requests import *
from fastapi import APIRouter, Request, Security, HTTPException, status
from security.api_keys import get_admin_key, key_handler
from utils.handlers import model_handler
from utils.handlers import llmkey_handler
import logging

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Security(get_admin_key)]
)

logger = logging.getLogger("admin")


# Admin endpoints
@router.post("/addapikey", status_code=status.HTTP_201_CREATED)
def addKey(RequestData: AddApiKeyRequest, admin_key: str = Security(get_admin_key)):
    if key_handler.add_key(
        user=RequestData.user, api_key=RequestData.key, name=RequestData.name
    ):
        pass
    else:
        raise HTTPException(409, "Key already exists")


@router.post("/removeapikey", status_code=status.HTTP_200_OK)
def removeKey(RequestData: AddApiKeyRequest, admin_key: str = Security(get_admin_key)):
    if key_handler.delete_key(key=RequestData.key):
        pass
    else:
        raise HTTPException(409, "Key already exists")


@router.post("/setllmkey", status_code=status.HTTP_200_OK)
def setllmKey(RequestData: LLMKeyRequest, admin_key: str = Security(get_admin_key)):
    llmkey_handler.set_key(RequestData.key)


@router.get("/listkeys", status_code=status.HTTP_200_OK)
def listKeys(RequestData: Request, admin_key: str = Security(get_admin_key)):
    logger.info("Keys requested")
    return key_handler.list_keys()

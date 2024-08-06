from .admin_requests import *
from fastapi import APIRouter, Request, Security, HTTPException, status, Depends
from security.api_keys import get_admin_key, key_handler
from utils.handlers import model_handler, logging_handler, admin_handler
import logging
from typing import Optional
from starlette.authentication import SimpleUser
from security.saml import get_admin_user

logger = logging.getLogger("admin")


def get_admin_auth(
    api_auth: Optional[str] = Depends(get_admin_key),
    session_auth: Optional[SimpleUser] = Depends(get_admin_user),
):
    logger.info("Checking admin authentication")
    if not api_auth == None or not session_auth == None:
        return True
    else:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication, or insufficient permissions",
        )


router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Security(get_admin_auth)]
)


# Admin endpoints
@router.post("/addmodel", status_code=status.HTTP_201_CREATED)
def addModel(
    RequestData: AddAvailableModelRequest, is_admin: bool = Security(get_admin_auth)
):
    # Add a new model, if the model already exists, return a 409
    # A Model needs a path (forward path to the model), a model name, and an owner
    # The assumption is, that the API provided by the model server is compatible with openAI API.
    try:
        model_handler.add_model(
            model=RequestData.model,
            owner=RequestData.owner,
            path=RequestData.target_path,
        )
    except KeyError as e:
        raise HTTPException(status.HTTP_409_CONFLICT)


@router.post("/removemodel", status_code=status.HTTP_200_OK)
def removemodel(
    RequestData: RemoveModelRequest, is_admin: bool = Security(get_admin_auth)
):
    try:
        model_handler.remove_model(RequestData.model)
    except KeyError as e:
        raise HTTPException(status.HTTP_410_GONE)


@router.post("/addapikey", status_code=status.HTTP_201_CREATED)
def addKey(RequestData: AddApiKeyRequest, is_admin: bool = Security(get_admin_auth)):
    if key_handler.add_key(
        user=RequestData.user, api_key=RequestData.key, name=RequestData.name
    ):
        pass
    else:
        raise HTTPException(409, "Key already exists")


@router.post("/removeapikey", status_code=status.HTTP_200_OK)
def removeKey(RequestData: AddApiKeyRequest, is_admin: bool = Security(get_admin_auth)):
    if key_handler.delete_key(key=RequestData.key):
        pass
    else:
        raise HTTPException(409, "Key already exists")


@router.get("/listkeys", status_code=status.HTTP_200_OK)
def listKeys(RequestData: Request, is_admin: bool = Security(get_admin_auth)):
    logger.debug("Keys requested")
    return key_handler.list_keys()


@router.post("/getusage", status_code=status.HTTP_200_OK)
def listKeys(
    RequestData: ObtainUsageRequest, is_admin: bool = Security(get_admin_auth)
):
    logger.info("Usage Data requested")
    return logging_handler.get_usage_by_user(
        from_time=RequestData.from_time,
        to_time=RequestData.to_time,
        user=RequestData.user,
    )


@router.get("/getusers", status_code=status.HTTP_200_OK)
def listKeys(RequestData: Request, is_admin: bool = Security(get_admin_auth)):
    return admin_handler.list_users()


@router.post("/makeadmin", status_code=status.HTTP_200_OK)
def listKeys(RequestData: MakeAdminRequest, is_admin: bool = Security(get_admin_auth)):
    return admin_handler.add_admin(RequestData.username)

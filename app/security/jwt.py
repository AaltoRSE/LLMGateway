from datetime import datetime, timedelta
from typing import Callable

from fastapi import HTTPException, status, Security
from fastapi.security import APIKeyHeader

from jose import JWTError, jwt
from pydantic import BaseModel


ACCESS_TOKEN_EXPIRE_MINUTES = 2
ALGORITHM = "HS256"
SECRET_KEY = "SomeSecret"
api_key_header = APIKeyHeader(name="Authorization")


class TokenRequest(BaseModel):
    token: str


class User(BaseModel):
    username: str
    attributes: dict


def checkUser(data):
    # Put in your user check here.
    return True


async def get_authed_user(api_key_header: str = Security(api_key_header)) -> User:
    """
    Retrieves and validates the API key from the header.

    Args:
    - api_key_header (str): Header containing the API key preceded by 'Bearer '.

    Returns:
    - str: The validated API key (without 'Bearer' prefix) if it passes the validation check.

    Raises:
    - HTTPException: If the provided API key is invalid or missing, it raises a 401 status code error
        with the detail "Invalid or missing API Key". Additionally, logs information about the header and key.
    """
    print("Trying to obtain user")
    if api_key_header != None:
        try:
            # This should get the token
            token = api_key_header.split(" ", 1)[1]
            user = await get_current_user(token)
            return user
        except JWTError as e:
            print("got a JWT error")
            print(e)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
                headers={"Authorization": "Bearer"},
            )
        except Exception as e:
            print("got a different error")
            print(e)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Authorization header.",
                headers={"Authorization": "Bearer"},
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No authorization provided",
            headers={"Authorization": "Bearer"},
        )


def create_access_token(data: dict, useracceptable: Callable = checkUser):
    createToken = useracceptable(dict)
    if createToken:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = data.copy()
        expire = datetime.now() + expires_delta
        to_encode.update({"exp": expire.timestamp()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not allowed to proceed",
            headers={"Authorization": "Bearer"},
        )


async def get_current_user(token: str) -> User:
    print(token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Authorization": "Bearer"},
    )
    # This does also check the expiration time stamp...
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user: User = User(username=payload.get("user"), attributes=payload)
    print(user)
    if user.username is None:
        raise credentials_exception

    if user.username is None:
        raise credentials_exception
    print("Returning user")
    return user

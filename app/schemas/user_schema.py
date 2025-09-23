"""
This module provides schemas for User entities and operations using Pydantic.
The schemas include base, creation, and update models for users.
"""

import re
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
from pydantic import AfterValidator, BaseModel
from typing_extensions import Annotated
from app.config import base_quota

possible_languages = Literal["en", "fi", "sv"]


class AuthData(BaseModel):
    auth_id: str
    first_name: str
    last_name: str


class SessionAuthData(AuthData):
    roles: List[str]
    additional_data: Optional[Dict[str, Any]] = None


# Base schema for users
#
# SECURITY: Note that each field in this model is exposed in get_user_details call, do not add sensitive items
class UserBase(AuthData):
    admin: bool
    accepted_agreement_version: str
    quota: float = base_quota


# User schema
#
# SECURITY: Note that each field in this model is exposed in get_user_details call, do not add sensitive items
class User(UserBase):
    id: str


class UserUpdate(BaseModel):
    auth_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    admin: Optional[bool] = None
    accepted_agreement_version: Optional[str] = None
    quota: Optional[float] = None


class LanguageUpdate(BaseModel):
    selected_language: possible_languages


# Response schema after updating an user
class UserUpdateResponse(BaseModel):
    id: int
    store_data: bool
    accepted_agreement_version: str
    last_active: datetime


# Validates that agreement version is digit(s).digit(s)
def is_valid_agreement_version(value: str) -> str:
    pattern = r"^\d+\.\d+$"
    if not re.match(pattern, value):
        raise ValueError(f"{value} is not a valid version in format of x.y")

    return value


# Input from agreement acceptance
class InputAcceptAgreement(BaseModel):
    accepted_agreement_version: Annotated[
        str, AfterValidator(is_valid_agreement_version)
    ]


# Schema for updating user details
#
# SECURITY: Logged in user controls the input here, do not add sensitive fields
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    accepted_agreement_version: Optional[
        Annotated[str, AfterValidator(is_valid_agreement_version)]
    ] = None

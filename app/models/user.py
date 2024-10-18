"""
This module provides schemas for User entities and operations using Pydantic.
The schemas include base, creation, and update models for users.
"""

from pydantic import BaseModel, Field
from typing import List


class UserData(BaseModel):
    auth_id: str
    first_name: str
    last_name: str
    admin: bool = False
    seen_guide_version: str = ""
    email: str = ""


# Base schema for users
class User(UserData):
    keys: List[str] = []

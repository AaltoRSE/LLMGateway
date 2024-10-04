"""
This module provides schemas for User entities and operations using Pydantic.
The schemas include base, creation, and update models for users.
"""

from pydantic import BaseModel


# Base schema for users
class User(BaseModel):
    auth_id: str
    first_name: str
    last_name: str
    admin: bool
    seen_guide_version: str

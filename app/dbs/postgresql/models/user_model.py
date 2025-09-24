"""
This module defines the user model.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Integer, String, DateTime, Float
from sqlalchemy.orm import mapped_column
from .base_model import BaseModelClass
from app.config import app_configuration


class User(BaseModelClass):
    """
     Represents a user in the system.

    Attributes:
         id (int): The user's unique identifier.
         auth_id (str): The authorization identifier for the user.
         first_name (str): The user's first name.
         last_name (str): The user's last name.
         admin (bool): Indicates whether the user has administrative privileges. Not used currently (2025-06)
         store_data (bool): Indicates whether the user has accepted that their conversation data can be stored to a database.
         accepted_agreement_version (bool): Indicates whether the user has accepted the latest agreement version.
         created_at (datetime): The timestamp when the user was created.
         last_active (datetime): The timestamp for the user's last login.
         seen_tiptour (bool): Indicates whether the user has seen the tiptour as a whole
    """

    __tablename__ = "users"

    id = mapped_column(
        Integer, primary_key=True, nullable=False, unique=True, autoincrement=True
    )
    auth_id = mapped_column(String(60), nullable=False, unique=True)
    first_name = mapped_column(String(40), nullable=False)
    last_name = mapped_column(String(60), nullable=False)
    admin = mapped_column(Boolean, nullable=False, default=False)
    accepted_agreement_version = mapped_column(String, nullable=False, default=False)
    quota = mapped_column(Float, default=app_configuration.base_quota, nullable=False)

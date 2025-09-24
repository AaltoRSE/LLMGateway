from sqlalchemy import String, Boolean, Integer, ForeignKey, Float
from sqlalchemy.orm import mapped_column
from .base_model import BaseModelClass
from .user_model import User


class APIKey(BaseModelClass):
    """
    Represents an API key in the database.

    Attributes:
        key (str): The API key string.
        user_id (int): The user associated with the API key.
        active (bool): Whether the API key is active.
        name (str): The name of the API key.
        service (str): A service this key is for
        quota (int): The monthly quota for the key.
    """

    __tablename__ = "api_keys"

    key = mapped_column(String, primary_key=True, nullable=False, unique=True)
    user_id = mapped_column(ForeignKey((User.id)), nullable=True)
    service = mapped_column(String, nullable=True)
    active = mapped_column(Boolean, default=True, nullable=False)
    name = mapped_column(String, nullable=False)
    quota = mapped_column(Float, nullable=True)

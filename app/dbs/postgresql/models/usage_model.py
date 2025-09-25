"""
This module defines the usage model.
"""

from datetime import datetime, timezone
from sqlalchemy import Integer, ForeignKey, String, DateTime, Float, BigInteger
from sqlalchemy.orm import mapped_column
from .base_model import BaseModelClass
from .user_model import User
from .key_model import APIKey


# Conversation model to define database logic
class Usage(BaseModelClass):
    """
    Represents a single interaction with a model that incurred a cost

    Attributes:
        id (int): The conversation's unique identifier.
        user_id (int): The ID of the user involved in the conversation.
        api_key (str): the api key used to create this
        prompt_tokens (int) : Optional, can contain the number of prompt tokens (for statistics)
        completion_tokens(int): Optional, can contain the number of completion tokens (for statistics)
        model (str): The used model for this usage (for statistics)
        timestamp (datetime): The timestamp, when the usage was generated
        cost (float): The cost (in €) this interaction incurred.

    """

    __tablename__ = "usage"

    id = mapped_column(
        BigInteger, primary_key=True, nullable=False, unique=True, autoincrement=True
    )
    user_id = mapped_column(Integer, ForeignKey(User.id), nullable=True)
    api_key = mapped_column(String, ForeignKey(APIKey.key), nullable=True)
    prompt_tokens = mapped_column(Integer, nullable=True)
    completion_tokens = mapped_column(Integer, nullable=True)
    model = mapped_column(String, nullable=False)
    cost = mapped_column(Float, nullable=False)
    timestamp = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

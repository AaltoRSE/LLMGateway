"""
This module defines the usage model.
"""

from datetime import datetime, timezone
from sqlalchemy import Integer, ForeignKey, String, DateTime, Float, BigInteger
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import mapped_column
from .base_model import BaseModelClass


# Conversation model to define database logic
class LLMModel(BaseModelClass):
    """
    Represents a single interaction with a model that incurred a cost

    Attributes:
        id (int): The conversation's unique identifier.
        user_id (int): The ID of the user involved in the conversation.
        prompt_tokens (int) : Optional, can contain the number of prompt tokens (for statistics)
        completion_tokens(int): Optional, can contain the number of completion tokens (for statistics)
        model (str): The used model for this usage (for statistics)
        timestamp (datetime): The timestamp, when the usage was generated
        cost (float): The cost (in €) this interaction incurred.

    """

    __tablename__ = "llmmodels"

    id = mapped_column(String, primary_key=True, nullable=False, unique=True)
    owned_by = mapped_column(String, nullable=False)
    permissions = mapped_column(ARRAY(String), default=[], nullable=False)
    object = mapped_column(String, default="model", nullable=False)
    type = mapped_column(ARRAY(String), default=["chat"], nullable=False)
    path = mapped_column(String, nullable=False)
    host = mapped_column(String, nullable=False)
    name = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=False)
    prompt_cost = mapped_column(float, nullable=False)
    completion_cost = mapped_column(float, nullable=False)
    cached_token_cost = mapped_column(float, nullable=False)

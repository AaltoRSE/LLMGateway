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

    """

    __tablename__ = "llmmodels"
    id = mapped_column(
        Integer, primary_key=True, nullable=False, unique=True, autoincrement=True
    )
    llm_model_id = mapped_column(String, primary_key=True, nullable=False, unique=True)
    owned_by = mapped_column(String, nullable=False)
    permissions = mapped_column(ARRAY(String), default=[], nullable=False)
    object = mapped_column(String, default="model", nullable=False)
    type = mapped_column(ARRAY(String), default=["chat"], nullable=False)
    path = mapped_column(String, nullable=False)
    host = mapped_column(String, nullable=False)
    name = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=False)
    prompt_cost = mapped_column(Float, nullable=False)
    completion_cost = mapped_column(Float, nullable=False)
    cached_token_cost = mapped_column(Float, nullable=False)

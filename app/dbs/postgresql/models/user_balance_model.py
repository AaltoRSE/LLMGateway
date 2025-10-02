"""
This module defines the usage model.
"""

from sqlalchemy import Integer, ForeignKey, Date, Float, String, UniqueConstraint
from sqlalchemy.orm import mapped_column
from .base_model import BaseModelClass
from .user_model import User
from .key_model import APIKey


# Conversation model to define database logic
class UserBalance(BaseModelClass):
    """
    Represents the balance of a user for a month

    Attributes:
        id (int): The balance identifier (for db use).
        user_id (int): The ID of the user the balance belongs to.
        balance_used (float) : The current balance used by the user
        total_balance (float) : The total balance for the period
        period (Date) : A String representing the relevant period. Will always point to the first of a Month

    """

    __tablename__ = "user_balance"

    id = mapped_column(
        Integer, primary_key=True, nullable=False, unique=True, autoincrement=True
    )
    user_id = mapped_column(Integer, ForeignKey(User.id), nullable=False, index=True)
    balance_used = mapped_column(Float, default=0.0, nullable=False)
    period = mapped_column(Date, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "period", name="user_per_period"),)

"""This module provides factory methods to generate repositories for fastapi dependency injection"""

# Convenience to allow import from here.
from typing import Type
from app.config.db import (
    UserRepositoryImpl,
    UsageRepositoryImpl,
    LLMModelRepositoryImpl,
    APIKeyRepositoryImpl,
    BalanceRepositoryImpl,
)
from app import repositories


def get_user_repository_class() -> Type[repositories.UserRepository]:
    """Get a user repository"""
    return UserRepositoryImpl


def get_usage_repository_class() -> Type[repositories.UsageRepository]:
    """Get a usage repository"""
    return UsageRepositoryImpl


def get_balance_repository_class() -> Type[repositories.BalanceRepository]:
    """Get a balance repository"""
    return BalanceRepositoryImpl


def get_llm_repository_class() -> Type[repositories.LLMModelRepository]:
    """Get a LLM Repository"""
    return LLMModelRepositoryImpl


def get_key_repository_class() -> Type[repositories.APIKeyRepository]:
    """Get a apikey Repository"""
    return APIKeyRepositoryImpl

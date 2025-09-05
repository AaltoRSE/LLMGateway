"""This module provides factory methods to generate repositories for fastapi dependency injection"""

# Convenience to allow import from here.
from typing import Type
from app.config.db import (
    UserRepositoryImpl,
    UsageRepositoryImpl,
    LLMRepositoryImpl,
    APIKeyRepositoryImpl,
)
from app import repositories


async def get_user_repository_class() -> Type[repositories.UserRepository]:
    """Get a user repository"""
    return UserRepositoryImpl


async def get_usage_repository_class() -> Type[repositories.UsageRepository]:
    """Get a usage repository"""
    return UsageRepositoryImpl


async def get_llm_repository_class() -> Type[repositories.LLMModelRepository]:
    """Get a LLM Repository"""
    return LLMRepositoryImpl


async def get_key_repository_class() -> Type[repositories.APIKeyRepositry]:
    """Get a LLM Repository"""
    return APIKeyRepositoryImpl

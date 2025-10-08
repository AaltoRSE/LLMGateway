"""
Database related configuration properties
"""

from typing import Type
from app import repositories
from app.config import app_configuration

user_db = app_configuration.databases.user_db.value
balance_db = app_configuration.databases.balance_db.value
apikey_db = app_configuration.databases.api_key_db.value
model_db = app_configuration.databases.model_db.value
usage_db = app_configuration.databases.usage_db.value

UserRepositoryImpl: Type[repositories.UserRepository] = repositories.UserRepository
LLMModelRepositoryImpl: Type[repositories.LLMModelRepository] = (
    repositories.LLMModelRepository
)
APIKeyRepositoryImpl: Type[repositories.APIKeyRepository] = (
    repositories.APIKeyRepository
)
BalanceRepositoryImpl: Type[repositories.BalanceRepository] = (
    repositories.BalanceRepository
)
UsageRepositoryImpl: Type[repositories.UsageRepository] = repositories.UsageRepository

# Load the correct database
if user_db == "postgresql":
    from app.dbs.postgresql import UserRepository

    UserRepositoryImpl = UserRepository

# This is just an example, on how this could be done for other databases
# elif user_db == "mongodb":
#    from app.dbs.mongodb import UserRepository
#    UserRepositoryImpl = UserRepository
else:
    raise ValueError("No valid user database found")

if balance_db == "postgresql":
    from app.dbs.postgresql import BalanceRepository

    BalanceRepositoryImpl = BalanceRepository
else:
    raise ValueError("No valid balance database found")


def get_model_repo() -> repositories.LLMModelRepository:
    """
    Convenience function to retrieve the api_key_repo for key init
    """
    raise NotImplementedError


if model_db == "postgresql":
    from app.dbs.postgresql import ModelRepository

    LLMModelRepositoryImpl = ModelRepository
    from app.dbs.postgresql.db import db

    # This needs to be done to be able to properly start up the system.
    def get_model_repo() -> (
        repositories.LLMModelRepository
    ):  # pylint: disable=function-redefined
        """
        Function implementation for postgresql
        """
        return ModelRepository(next(db.get_db()))

else:
    raise ValueError("No valid model database found")


def get_api_key_repo() -> repositories.APIKeyRepository:
    """
    Convenience function to retrieve the api_key_repo for key init
    """
    raise NotImplementedError


if apikey_db == "postgresql":
    from app.dbs.postgresql import APIKeyRepository

    APIKeyRepositoryImpl = APIKeyRepository
    from app.dbs.postgresql.db import db

    # This needs to be done to be able to properly start up the system.
    def get_api_key_repo() -> (
        repositories.APIKeyRepository
    ):  # pylint: disable=function-redefined
        """
        Function implementation for postgresql
        """
        return APIKeyRepository(next(db.get_db()))

else:
    raise ValueError("No valid key database found")

if usage_db == "postgresql":
    from app.dbs.postgresql import UsageRepository

    UsageRepositoryImpl = UsageRepository
else:
    raise ValueError("No valid usage database found")

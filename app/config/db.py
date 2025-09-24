import os
import json
from typing import List, Optional, Dict, TypedDict, Type
from app import repositories
from app.config import app_configuration


class DatabaseConfig(TypedDict):
    options: List[str]
    default: str
    current: Optional[str]


# We will need a bunch of potential environment variables to check on what services to use for which type of data.
Databases: Dict[str, DatabaseConfig] = {
    "UserDB": {"options": ["postgresql"], "default": "postgresql", "current": None},
    "ModelDB": {
        "options": ["postgresql"],
        "default": "postgresql",
        "current": None,
    },
    "BalanceDB": {"options": ["postgresql"], "default": "postgresql", "current": None},
    "APIKeyDB": {"options": ["postgresql"], "default": "postgresql", "current": None},
    "UsageDB": {"options": ["postgresql"], "default": "postgresql", "current": None},
}

# Load all options
for db in Databases:
    if db in app_configuration and [db] in Databases[db]["options"]:
        Databases[db]["current"] = app_configuration[db]
    else:
        Databases[db]["current"] = Databases[db]["default"]

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
    raise Exception("No valid user database found")

if balance_db == "postgresql":
    from app.dbs.postgresql import BalanceRepository

    BalanceRepositoryImpl = BalanceRepository

if model_db == "postgresql":
    from app.dbs.postgresql import ModelRepository

    LLMModelRepositoryImpl = ModelRepository


def get_api_key_repo() -> repositories.APIKeyRepository:
    raise NotImplementedError


if apikey_db == "postgresql":
    from app.dbs.postgresql import APIKeyRepository

    APIKeyRepositoryImpl = APIKeyRepository
    from app.dbs.postgresql.db import db

    def get_api_key_repo() -> repositories.APIKeyRepository:
        return APIKeyRepository(next(db.get_db()))


if usage_db == "postgresql":
    from app.dbs.postgresql import UsageRepository

    UsageRepositoryImpl = UsageRepository

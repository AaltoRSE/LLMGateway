"""
Application configuration code
"""

import os
import json
from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class MyEnum(str, Enum):
    """
    Helper class for enums used in pydantic.
    """

    def toJSON(self) -> str:  # pylint: disable=invalid-name
        """
        Convert to JSON, required for pydantic model validation and dumping
        """
        return self.value


class DBOptions(MyEnum):
    """
    Possibe database options
    """

    POSTGRESQL = "postgresql"


class DBConfig(BaseModel):
    """
    Database configuration settings
    """

    user_db: DBOptions = Field(DBOptions.POSTGRESQL)
    api_key_db: DBOptions = Field(DBOptions.POSTGRESQL)
    balance_db: DBOptions = Field(DBOptions.POSTGRESQL)
    usage_db: DBOptions = Field(DBOptions.POSTGRESQL)
    model_db: DBOptions = Field(DBOptions.POSTGRESQL)


class Configuration(BaseModel):
    """App configuration settings"""

    databases: DBConfig
    base_quota: float
    current_agreement_version: str
    session_expiration_time: int
    default_embedding_model: str
    default_chat_model: str
    allowed_groups: List[str]


current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "config.json")

with open(file_path, "r", encoding="utf-8") as f:
    app_configuration = Configuration.model_validate(json.loads(f.read()))

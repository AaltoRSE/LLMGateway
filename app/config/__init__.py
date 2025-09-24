import os
import json
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class MyEnum(str, Enum):
    def toJSON(self) -> str:
        return self.value


class DBOptions(MyEnum):
    postgresql = "postgresql"


class DBConfig(BaseModel):
    user_db: Optional[DBOptions] = Field(DBOptions.postgresql)
    api_key_db: Optional[DBOptions] = Field(DBOptions.postgresql)
    balance_db: Optional[DBOptions] = Field(DBOptions.postgresql)
    usage_db: Optional[DBOptions] = Field(DBOptions.postgresql)
    model_db: Optional[DBOptions] = Field(DBOptions.postgresql)


class Configuration(BaseModel):
    databases: DBConfig
    base_quota: float
    current_agreement_version: str
    session_expiration_time: int


current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "config.json")

with open(file_path, "r") as f:
    app_configuration = Configuration.model_validate(json.loads(f.read()))

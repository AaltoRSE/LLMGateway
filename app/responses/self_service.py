from pydantic import BaseModel
from typing import List
from app.schemas.usage_schema import UserAndKeyUsageData


class ModelDescription(BaseModel):
    prompt_cost: float
    completion_cost: float
    name: str
    description: str
    id: str
    type: str


ModelListResponse = List[ModelDescription]


class UsageResponse(UserAndKeyUsageData):
    quota: float
    balance: float

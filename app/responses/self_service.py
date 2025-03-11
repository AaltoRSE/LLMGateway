from pydantic import BaseModel
from typing import List


class ModelDescription(BaseModel):
    prompt_cost: float
    completion_cost: float
    name: str
    description: str
    id: str
    type: str


ModelListResponse = List[ModelDescription]

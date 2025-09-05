from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, RootModel, Field
from app.schemas.llmmodel_schema import model_type


class LLMModel(BaseModel):
    id: str
    owned_by: str
    permissions: Optional[List[str]] = []
    object: Optional[str] = Field(default="model")
    type: Optional[List[model_type]] = ["chat"]
    path: str
    host: str
    name: str
    description: str
    prompt_cost: float = 0.0001
    completion_cost: float = 0.0001
    cached_token_cost: float = 0.00001

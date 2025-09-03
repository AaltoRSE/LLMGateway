from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, RootModel, Field

model_type = Literal["TextGeneration", "Embedding"]


class LLMModelData(BaseModel):
    id: str
    owned_by: str
    permissions: Optional[List[str]] = []
    object: Optional[str] = Field(default="model")
    type: Optional[List[model_type]] = ["TextGeneration"]


class LLMModel(BaseModel):
    path: str
    host: str
    model: LLMModelData
    name: str
    description: str
    prompt_cost: float = 0.0001
    completion_cost: float = 0.0001


class LLMModelDict(RootModel):
    root: Dict[str, LLMModel]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self):
        return len(self.root)

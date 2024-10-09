from typing import List, Dict
from pydantic import BaseModel, RootModel, Field


class LLMModelData(BaseModel):
    id: str
    owned_by: str
    permissions: List[str] = []
    object: str = Field(default="model")


class LLMModel(BaseModel):
    path: str
    model: LLMModelData
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

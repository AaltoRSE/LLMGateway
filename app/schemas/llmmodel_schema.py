from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, RootModel, Field

model_types = ["chat", "embedding", "responses"]
model_type = Literal[*model_types]


class LLMModelDataDetails(BaseModel):
    id: str
    owned_by: str
    permissions: Optional[List[str]] = []
    object: Optional[str] = Field(default="model")
    type: Optional[List[model_type]] = ["chat"]


class LLMModelData(BaseModel):
    path: str
    host: str
    model: LLMModelDataDetails
    name: str
    description: str
    prompt_cost: float = 0.0001
    completion_cost: float = 0.0001
    cached_token_cost: float = 0.00001
    protocol: Optional[str] = "html"


class LLMModelDict(RootModel):
    root: Dict[str, LLMModelData]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self):
        return len(self.root)

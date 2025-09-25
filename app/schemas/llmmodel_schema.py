from typing import List, Dict, Literal, Optional, Generator, Any
from pydantic import BaseModel, RootModel, Field

model_types = ["chat", "embedding", "responses"]
model_type = Literal[*model_types]  # type: ignore[valid-type]


class LLMModelDataDetails(BaseModel):
    id: str
    owned_by: str
    permissions: Optional[List[str]] = []
    object: Optional[str] = Field(default="model")
    type: List[model_type] = Field(["chat"])  # type: ignore[valid-type]


class LLMPublicData(BaseModel):
    model: LLMModelDataDetails
    name: str
    description: str
    prompt_cost: float = 0.0001
    completion_cost: float = 0.0001
    cached_token_cost: float = 0.00001


class LLMModelData(LLMPublicData):
    path: (
        str  # This is the actual path the model is called under (before /v1/<endpoint>)
    )
    host: str  # This is the host header used for the requests.
    # This may differ from the path since it is used by kubernetes to select
    # the actual worker


class LLMModelDict(RootModel):
    root: Dict[str, LLMModelData]

    def __iter__(
        self,
    ) -> Generator[tuple[str, Any], None, None]:
        return iter(self.root)  # type: ignore[arg-type]

    def __getitem__(self, item: str) -> LLMModelData:
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

from pydantic import BaseModel, model_validator
from typing import Optional, Self


class APIKey(BaseModel):
    key: str
    user: Optional[str] = None
    service: Optional[str] = None
    active: bool
    name: Optional[str] = None
    quota: Optional[float] = None

    @model_validator(mode="after")
    def check_one_source_exists(self) -> Self:
        if self.user is None and self.service is None:
            raise ValueError("Missing Source! Either user or key has to be non None")
        return self

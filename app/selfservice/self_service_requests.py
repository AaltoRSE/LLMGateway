from pydantic import BaseModel, Field
from datetime import date


class CreateKeyRequest(BaseModel):
    name: str = Field(description="Name of the key (for association - human readble).")


class DeleteKeyRequest(BaseModel):
    key: str = Field(description="the key to delete")


class ObtainUsageRequest(BaseModel):
    from_time: date = Field(description="The oldest time to check", default=None)
    to_time: date = Field(description="The latest time to check", default=None)

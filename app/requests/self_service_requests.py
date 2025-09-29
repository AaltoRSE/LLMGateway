from pydantic import BaseModel, Field
from datetime import datetime


class CreateKeyRequest(BaseModel):
    name: str = Field(description="Name of the key (for association - human readble).")


class DeleteKeyRequest(BaseModel):
    key: str = Field(description="the key to delete")


class ObtainUsageRequest(BaseModel):
    from_time: datetime | None = Field(
        description="The oldest time to check", default=None
    )
    to_time: datetime | None = Field(
        description="The latest time to check", default=None
    )


class KeyUsageRequest(ObtainUsageRequest):
    key: str = Field(description="the key to get data for")


class AcceptAgreement(BaseModel):
    version: str = Field(description="Version that has been accepted.")

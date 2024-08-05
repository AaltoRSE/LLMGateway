from pydantic import BaseModel, Field
from datetime import date

model_field = Field(description="The name of the Model")


class AddAvailableModelRequest(BaseModel):
    model: str = model_field
    target_path: str = Field(description="The target path on the inference server.")
    owner: str = Field(description="Who owns the model")


class AddApiKeyRequest(BaseModel):
    user: str = Field(description="The user with whom to associate the key.")
    key: str = Field(description="The key to add.")
    name: str = Field(description="The name of the key")


class RemoveModelRequest(BaseModel):
    model: str = model_field


class RemoveKeyRequest(BaseModel):
    key: str = Field(description="The key to add.")


class MakeAdminRequest(BaseModel):
    username: str = Field(description="The name of the admin user to add.")


class LoginRequest(BaseModel):
    key: str = Field(description="The key to add.")


class ObtainUsageRequest(BaseModel):
    from_time: date = Field(description="The oldest time to check", default=None)
    to_time: date = Field(description="The latest time to check", default=None)

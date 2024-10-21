from pydantic import BaseModel, Field
from app.requests.general_requests import UserRequest

model_field = Field(description="The id of the model")
model_name = Field(
    description="The name of the model. E.g. if ID is 'google/gemma2-27b', the name could be 'Gemma 2 - 27B'"
)
model_description = Field(description="A more extensive description of the model")


class AddAvailableModelRequest(BaseModel):
    id: str = model_field
    target_path: str = Field(description="The target path on the inference server.")
    name: str = model_name
    description: str = model_description
    prompt_cost: float = Field(
        description="The cost of a prompt_token", default=0.01 / 1000
    )
    completion_cost: float = Field(
        description="The cost of a completion token", default=0.01 / 1000
    )


class AddApiKeyRequest(BaseModel):
    user: str = Field(description="The user with whom to associate the key.")
    key: str = Field(description="The key to add.")
    name: str = Field(description="The name of the key")


class RemoveModelRequest(BaseModel):
    model: str = model_field


class RemoveKeyRequest(BaseModel):
    key: str = Field(description="The key to add.")


class LoginRequest(BaseModel):
    key: str = Field(description="The key to add.")


class LoginRequest(BaseModel):
    key: str = Field(description="The key to add.")


class SetAdminRequest(UserRequest):
    admin: bool = Field(description="Whether the user should be an admin or not")

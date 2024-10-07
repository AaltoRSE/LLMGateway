from pydantic import BaseModel, Field

model_field = Field(description="The name of the Model")


class AddAvailableModelRequest(BaseModel):
    model: str = model_field
    target_path: str = Field(description="The target path on the inference server.")
    owner: str = Field(description="Who owns the model")
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

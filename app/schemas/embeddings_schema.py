"""This is a placeholder class for initial requests"""

from pydantic import BaseModel

from typing import Optional, Any, Callable, Literal

from openai.types.create_embedding_response import CreateEmbeddingResponse

from app.schemas.usage_schema import APIRequest
from app.security.auth import BackendUser


class EmbeddingRequest(BaseModel):
    input: str
    model: str
    dimensions: Optional[int] = None
    encoding_format: Optional[Literal["float", "base64"] ] = None


class EmbeddingModel():
    # Implementing classes have to define the model name and url
    name: str
    url: str

    def embed(
        self,
        user: BackendUser,
        request: EmbeddingRequest,
        usage_callback: Callable[[APIRequest], Any],
    ) -> CreateEmbeddingResponse:
        """
        Function that needs to call the Actual model and return the correct Embedding response obtained from the model.

        Args:
            user (BackendUser): The user making the request. Used for authentication The auth-token for the user is in user.auth_token.
            request (EmbeddingRequest): The embedding request containing the input text, model name, and optional parameters like dimensions and encoding format.
            usage_callback (Callable[[APIRequest], None]): A callback function to log or process token usage. MUST be called otherwise usage of the model goes unlogged.

        Returns:
            EmbeddingResponse: A list of integers representing the embedding vector for the input.

        Raises:
            NotImplementedError: This method must be implemented by subclasses to interact with the actual embedding model.

        """
        raise NotImplementedError("Needs to be implemented")

"""This class implements all the different Request handling mechanisms"""

from datetime import datetime
from typing import Callable, Any, AsyncIterator, Literal, Dict, Awaitable
import os

import httpx
from sse_starlette import ServerSentEvent

from fastapi import HTTPException
from sse_starlette import ServerSentEvent

from app.schemas.openai_schemas import (
    CreateChatCompletionRequest as ChatCompletionRequest,
)
from app.schemas.openai_schemas import (
    CreateChatCompletionResponse as ChatCompletionResponse,
)
from app.schemas.openai_schemas import CreateResponse
from app.schemas.openai_schemas import Response1 as CreateResponseResponse
from app.schemas.openai_schemas import (
    CreateEmbeddingRequest,
    CreateEmbeddingResponse,
    CompletionUsage,
    ResponseUsage,
)
from app.schemas.usage_schema import APIRequest
from app.schemas.llmmodel_schema import LLMModelData
from app.security.auth import BackendUser
from app.utils.stream_handling import process_completion_stream, process_response_stream

inference_key = os.environ.get("INFERENCE_KEY")


class LLMModel:
    def __init__(self, model: LLMModelData):
        self.model: LLMModelData = model
        # Need to figure out, whether this is the correct approach here.
        self.client: httpx.AsyncClient = (
            httpx.AsyncClient()
        )  # Initialize the HTTP client

    def __del__(self):
        # Ensure the client is closed when the object is garbage collected
        if not self.client.is_closed:
            import asyncio

            asyncio.run(self.client.aclose())  # Close the client asynchronously

    def calc_cost_from_chat_usage(self, usage: CompletionUsage) -> float:
        completion_tokens = usage.completion_tokens

        prompt_tokens = usage.prompt_tokens
        cached_tokens = 0
        if (
            usage.prompt_tokens_details is not None
            and usage.prompt_tokens_details.cached_tokens is not None
        ):
            prompt_tokens -= usage.prompt_tokens_details.cached_tokens
            cached_tokens = usage.prompt_tokens_details.cached_tokens
        return (
            completion_tokens * self.model.completion_cost / 1_000_000
            + prompt_tokens * self.model.prompt_cost / 1_000_000
            + cached_tokens * self.model.cached_token_cost / 1_000_000
        )

    def calc_cost_from_response_usage(self, usage: ResponseUsage) -> float:
        completion_tokens = usage.output_tokens

        prompt_tokens = usage.input_tokens
        cached_tokens = usage.input_tokens_details.cached_tokens
        # This is likely to be changing, since it currently does NOT contain cached tokens...
        # if (
        #    not usage.input_token_details is None
        #    and not usage.prompt_tokens_details.cached_tokens is None
        # ):
        #    prompt_tokens -= usage.prompt_tokens_details.cached_tokens
        #    cached_tokens = usage.prompt_tokens_details.cached_tokens
        return (
            completion_tokens * self.model.completion_cost / 1_000_000
            + prompt_tokens * self.model.prompt_cost / 1_000_000
            + cached_tokens * self.model.cached_token_cost / 1_000_000
        )

    async def filter_response_stream(
        self,
        stream: AsyncIterator[Any],
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
    ) -> AsyncIterator[ServerSentEvent]:
        """
        Yields items from the stream unless check_fn(item) is True, in which case on_match(item) is called instead.
        """
        async for item in stream:
            tokens, event, data = process_response_stream(item)
            if tokens is not None:
                await usage_callback(
                    APIRequest(
                        model=self.model.model.id,
                        prompt_tokens=tokens.input_tokens,
                        completion_tokens=tokens.output_tokens,
                        cost=self.calc_cost_from_response_usage(tokens),
                        timestamp=datetime.now(),
                    )
                )
            yield ServerSentEvent(data=data, event=event)

    async def filter_chat_stream(
        self,
        stream: AsyncIterator[Any],
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
        filter_usage: bool,
    ) -> AsyncIterator[Any]:
        """
        Yields items from the stream unless check_fn(item) is True, in which case on_match(item) is called instead.
        """
        async for item in stream:
            tokens, data = process_completion_stream(item)
            if tokens is not None:
                await usage_callback(
                    APIRequest(
                        model=self.model.model.id,
                        prompt_tokens=tokens.prompt_tokens,
                        completion_tokens=tokens.completion_tokens,
                        cost=self.calc_cost_from_chat_usage(tokens),
                        timestamp=datetime.now(),
                    )
                )
                if filter_usage:
                    # Skip the usage chunk, since the user did not request it.
                    continue
            yield ServerSentEvent(data=data)

    async def stream_chat_request(
        self,
        request: ChatCompletionRequest,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
        filter_usage: bool = False,
    ) -> AsyncIterator[ServerSentEvent]:
        """
        Function that needs to call the Actual model and return an Iterator for the responses.
        FIXME: Possibly, the type of this iterator needs to be changed (potentially it needs to be a bytes iterator)...

        Args:
            user (BackendUser): The user making the request. Used for authentication The auth-token for the user is in user.auth_token.
            request (ChatCompletionRequest): The chat completion request
            usage_callback (Callable[[APIRequest], None]): A callback function to log or process token usage. MUST be called otherwise usage of the model goes unlogged.
                                                           NOTE: the implementing model might need to add a "stream_options" parameter to the request, in order to obtain the
                                                                 usage token, and not send this token to the user if they did not request it.
        Returns:
            AsyncIterator: A iterator over the chunks.

        Raises:
            NotImplementedError: This method must be implemented by subclasses to interact with the actual embedding model.

        """
        if not "chat" in self.model.model.type:
            raise HTTPException(
                404, "This model does not offer streamed chat completions"
            )
        request_data = request.model_dump()
        print(f"Sending request to: {self.model.path}/v1/chat/completions")
        httpx_request = httpx.Request(
            method="POST",
            url=f"{self.model.host}{self.model.path}/v1/chat/completions",
            json=request_data,
            headers={
                "Authorization": f"{inference_key}",
                "Host": f"{self.model.host}",
            },  # SECURITY: forwarding authentication token
        )
        model_response = await self.client.send(httpx_request, stream=True)

        return self.filter_chat_stream(
            model_response.aiter_text(), usage_callback, filter_usage
        )

    async def non_stream_chat_request(
        self,
        request: ChatCompletionRequest,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
    ) -> ChatCompletionResponse:
        """
        Function that needs to call the Actual model and return a ChatResponse compatible with openAI responses

        Args:
            user (BackendUser): The user making the request. Used for authentication The auth-token for the user is in user.auth_token.
            request (ChatCompletionRequest): The chat completion request
            usage_callback (Callable[[APIRequest], None]): A callback function to log or process token usage. MUST be called otherwise usage of the model goes unlogged.

        Returns:
            ChatResponse: An openAI Compatible chat response

        Raises:
            NotImplementedError: This method must be implemented by subclasses to interact with the actual embedding model.

        """
        if not "chat" in self.model.model.type:
            raise HTTPException(404, "This model does not offer chat completions")
        request_data = request.model_dump()
        print(
            f"Sending request to: {self.model.host}{self.model.path}/v1/chat/completions"
        )
        model_response = httpx.post(
            url=f"{self.model.host}{self.model.path}/v1/chat/completions",
            json=request_data,
            headers={"Authorization": f"{inference_key}", "Host": f"{self.model.host}"},
        )
        print(model_response.json())
        return_value = ChatCompletionResponse.model_validate(model_response.json())
        usage = return_value.usage
        await usage_callback(
            APIRequest(
                model=self.model.model.id,
                prompt_tokens=0 if usage is None else usage.prompt_tokens,
                completion_tokens=0 if usage is None else usage.completion_tokens,
                cost=0 if usage is None else self.calc_cost_from_chat_usage(usage),
                timestamp=datetime.now(),
            )
        )
        return return_value

    async def stream_response_request(
        self,
        request: CreateResponse,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
    ) -> AsyncIterator[ServerSentEvent]:
        """
        Function that needs to call the Actual model and return an Iterator for the responses.
        FIXME: Possibly, the type of this iterator needs to be changed (potentially it needs to be a bytes iterator)...

        Args:
            user (BackendUser): The user making the request. Used for authentication The auth-token for the user is in user.auth_token.
            request (CreateResponse): The response request
            usage_callback (Callable[[APIRequest], None]): A callback function to log or process token usage. MUST be called otherwise usage of the model goes unlogged.
                                                           NOTE: the implementing model might need to add a "stream_options" parameter to the request, in order to obtain the
                                                                 usage token, and not send this token to the user if they did not request it.
        Returns:
            AsyncIterator: A iterator over the chunks.

        Raises:
            NotImplementedError: This method must be implemented by subclasses to interact with the actual embedding model.

        """
        if not "responses" in self.model.model.type:
            raise HTTPException(404, "This model does not offer response backend")
        request_data = request.model_dump()
        httpx_request = httpx.Request(
            method="POST",
            url=f"{self.model.host}{self.model.path}/v1/responses",
            json=request_data,
            headers={"Authorization": f"{inference_key}", "Host": f"{self.model.host}"},
        )
        model_response = await self.client.send(httpx_request, stream=True)

        return self.filter_response_stream(model_response.aiter_text(), usage_callback)

    async def non_stream_response_request(
        self,
        request: CreateResponse,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
    ) -> CreateResponseResponse:
        """
        Function that needs to call the Actual model and return a ChatResponse compatible with openAI responses

        Args:
            user (BackendUser): The user making the request. Used for authentication The auth-token for the user is in user.auth_token.
            request (ChatCompletionRequest): The response request
            usage_callback (Callable[[APIRequest], None]): A callback function to log or process token usage. MUST be called otherwise usage of the model goes unlogged.

        Returns:
            CreateResponseResponse: An openAI Compatible chat response

        Raises:
            NotImplementedError: This method must be implemented by subclasses to interact with the actual embedding model.

        """
        if not "responses" in self.model.model.type:
            raise HTTPException(404, "This model does not offer non streamed responses")
        request_data = request.model_dump()
        model_response = httpx.post(
            url=f"{self.model.host}{self.model.path}/v1/responses",
            json=request_data,
            headers={"Authorization": f"{inference_key}", "Host": f"{self.model.host}"},
        )
        return_value = CreateResponseResponse.model_validate(model_response.json())
        usage = return_value.usage
        await usage_callback(
            APIRequest(
                model=self.model.model.id,
                prompt_tokens=0 if usage is None else usage.input_tokens,
                completion_tokens=0 if usage is None else usage.output_tokens,
                cost=0 if usage is None else self.calc_cost_from_response_usage(usage),
                timestamp=datetime.now(),
            )
        )
        return return_value

    async def embed(
        self,
        request: CreateEmbeddingRequest,
        usage_callback: Callable[[APIRequest], Any],
    ) -> CreateEmbeddingResponse:
        if not "embedding" in self.model.model.type:
            raise HTTPException(404, "This model does not offer non streamed responses")
        request_data = request.model_dump()
        model_response = httpx.post(
            url=f"{self.model.host}{self.model.path}/v1/embeddings",
            json=request_data,
            headers={
                "Authorization": f"{inference_key}",
                "Host": f"{self.model.host}",
            },  # SECURITY: forwarding authentication token
        )
        embeddings = CreateEmbeddingResponse.model_validate(model_response.json())
        await usage_callback(
            APIRequest(
                model=self.model.model.id,
                prompt_tokens=embeddings.usage.prompt_tokens,
                completion_tokens=embeddings.usage.total_tokens
                - embeddings.usage.prompt_tokens,
                cost=embeddings.usage.total_tokens * self.model.prompt_cost / 1000000,
                timestamp=datetime.now(),
            )
        )
        return embeddings

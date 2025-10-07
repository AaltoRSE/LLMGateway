"""This class implements all the different Request handling mechanisms"""

from datetime import datetime
from typing import Callable, Any, AsyncIterator, Awaitable, List
import os
import logging

import httpx
from sse_starlette import ServerSentEvent
from fastapi import HTTPException, Request, Response


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
from app.utils.stream_handling import process_completion_stream, process_response_stream

inference_key = os.environ.get("INFERENCE_KEY")

logger = logging.getLogger("app")


class LLMModel:
    """
    Instance for LLM model usage. Forwards requests to
    OpenAI compatible endpoints

    """

    def __init__(self, model: LLMModelData):
        """
        Constructor
        """
        self.model: LLMModelData = model

    def check_type(self, type: str):
        if not type in self.model.model.type:
            raise HTTPException(404, "This model does not offer {type} functionality")

    def build_request(
        self, request: dict[str, Any], path: str, add_stream_data: bool = False
    ) -> httpx.Request:
        """
        Build the request that's being sent to the models
        """
        if add_stream_data:
            # We add usage
            if not "stream_options" in request:
                request["stream_options"] = {"include_usage": True}
            else:
                request["stream_options"]["include_usage"] = True
        logger.debug(request)
        return httpx.Request(
            method="POST",
            url=f"{self.model.path}{path}",
            json=request,
            headers={
                "Authorization": f"Bearer {inference_key}",
                "Host": f"{self.model.host}",
                "Content-Type": "application/json",
            },  # SECURITY: forwarding authentication token
        )

    def calc_cost_from_chat_usage(self, usage: CompletionUsage) -> float:
        """
        Calculate cost for the usage from a chat completion request
        """
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
        """
        Calculate cost for the usage from a response request
        """
        completion_tokens = usage.output_tokens

        prompt_tokens = usage.input_tokens
        cached_tokens = usage.input_tokens_details.cached_tokens
        # This is likely to be changing, since it currently does NOT
        # contain cached tokens...
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
        item: Any,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
    ) -> AsyncIterator[ServerSentEvent]:
        """
        Yields items from the stream unless check_fn(item) is True, in which case
        on_match(item) is called instead.
        """
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
        return ServerSentEvent(data=data, event=event)

    async def filter_chat_stream(
        self,
        item: Any,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
        filter_usage: bool,
    ) -> List[ServerSentEvent]:
        """
        Yields items from the stream unless check_fn(item) is True, in which case
        on_match(item) is called instead.
        """
        logger.debug(item)
        tokens, data = process_completion_stream(item, filter_usage)
        logger.debug(data)
        if tokens is not None:
            logger.debug("Logging data")
            await usage_callback(
                APIRequest(
                    model=self.model.model.id,
                    prompt_tokens=tokens.prompt_tokens,
                    completion_tokens=tokens.completion_tokens,
                    cost=self.calc_cost_from_chat_usage(tokens),
                    timestamp=datetime.now(),
                )
            )
        return [ServerSentEvent(data=datum) for datum in data]

    async def check_response(self, response: httpx.Response):
        if not response.is_success:
            response_message = await response.text()
            logger.warning(
                "Request to model failed with %s, %s",
                response.status_code,
                response_message,
            )
            raise HTTPException(response.status_code, response_message)

    async def stream_chat_request(
        self,
        request: Request,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
        filter_usage: bool = False,
    ) -> AsyncIterator[ServerSentEvent]:
        """
        Function that needs to call the Actual model and return an Iterator for
        the responses.
        FIXME: Possibly, the type of this iterator needs to be changed (potentially
        it needs to be a bytes iterator)...

        Args:
            user (BackendUser): The user making the request. Used for authentication
                                The auth-token for the user is in user.auth_token.
            request (ChatCompletionRequest): The chat completion request
            usage_callback (Callable[[APIRequest], None]):
                                A callback function to log or process token usage. MUST
                                be called otherwise usage of the model goes unlogged.
                                NOTE: the implementing model might need to add a
                                "stream_options" parameter to the request, in order to
                                obtain the  usage token, and not send this token to the
                                user if they did not request it.
        Returns:
            AsyncIterator: A iterator over the chunks.

        Raises:
            NotImplementedError: This method must be implemented by subclasses
            to interact with the actual embedding model.

        """

        request_data = await request.json()
        forwarded_request = self.build_request(
            request=request_data,
            path="/v1/chat/completions",
            add_stream_data=filter_usage,
        )
        client: httpx.AsyncClient = request.app.state.httpx_client
        # This is hackish and should work with request.state.httpx_client
        response = await client.send(forwarded_request, stream=True)
        await self.check_response(response)

        async for item in response.aiter_text():
            processed_items = await self.filter_chat_stream(
                item, usage_callback, filter_usage
            )
            for processed_item in processed_items:
                yield processed_item

    async def non_stream_chat_request(
        self,
        request: Request,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
    ) -> ChatCompletionResponse:
        """
        Function that needs to call the Actual model and return a ChatResponse
        compatible with openAI responses

        Args:
            user (BackendUser): The user making the request. Used for authentication
                                The auth-token for the user is in user.auth_token.
            request (ChatCompletionRequest): The chat completion request
            usage_callback (Callable[[APIRequest], None]):
                                A callback function to log or process token usage.
                                MUST be called otherwise usage of the model goes unlogged.

        Returns:
            ChatResponse: An openAI Compatible chat response

        Raises:
            NotImplementedError: This method must be implemented by
                                subclasses to interact with the actual embedding model.

        """
        if not "chat" in self.model.model.type:
            raise HTTPException(404, "This model does not offer chat completions")
        request_data = await request.json()
        httpx_request = self.build_request(
            request=request_data, path="/v1/chat/completions"
        )
        client: httpx.AsyncClient = request.app.state.httpx_client
        # This is hackish and should work with request.state.httpx_client
        model_response = await client.send(httpx_request)
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
        request: Request,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
    ) -> AsyncIterator[ServerSentEvent]:
        """
        Function that needs to call the Actual model and return an Iterator for
        the responses.
        FIXME: Possibly, the type of this iterator needs to be changed
        (potentially it needs to be a bytes iterator)...

        Args:
            request (CreateResponse): The response request
            usage_callback (Callable[[APIRequest], None]):
                            A callback function to log or process token usage. MUST be
                            called otherwise usage of the model goes unlogged.
                            NOTE: the implementing model might need to add a "stream_options"
                            parameter to the request, in order to obtain the usage token, and
                            not send this token to the user if they did not request it.
        Returns:
            AsyncIterator: A iterator over the chunks.

        Raises:
            NotImplementedError: This method must be implemented by subclasses to
            interact with the actual embedding model.

        """

        request_data = await request.json()
        forwarded_request = self.build_request(
            request=request_data, path="/v1/responses"
        )
        client: httpx.AsyncClient = request.app.state.httpx_client
        model_response = await client.send(forwarded_request, stream=True)
        await self.check_response(model_response)
        async for item in model_response.aiter_text():
            processed_item = await self.filter_response_stream(item, usage_callback)
            if processed_item is not None:
                yield processed_item

    async def non_stream_response_request(
        self,
        request: Request,
        usage_callback: Callable[[APIRequest], Awaitable[Any]],
    ) -> CreateResponseResponse:
        """
        Function that needs to call the Actual model and return a ChatResponse
        compatible with openAI responses

        Args:
            user (BackendUser): The user making the request. Used for authentication
                                The auth-token for the user is in user.auth_token.
            request (ChatCompletionRequest): The response request
            usage_callback (Callable[[APIRequest], None]):
                        A callback function to log or process token usage.
                        MUST be called otherwise usage of the model goes unlogged.

        Returns:
            CreateResponseResponse: An openAI Compatible chat response

        Raises:
            NotImplementedError: This method must be implemented by
            subclasses to interact with the actual embedding model.

        """
        if not "responses" in self.model.model.type:
            raise HTTPException(404, "This model does not offer non streamed responses")
        request_data = await request.json()
        httpx_request = self.build_request(request=request_data, path="/v1/responses")
        client: httpx.AsyncClient = request.app.state.httpx_client
        model_response = await client.send(httpx_request)
        await self.check_response(model_response)
        return_value = CreateResponseResponse.model_validate(model_response.json())
        usage = return_value.usage
        await usage_callback(
            APIRequest(
                model=self.model.model.id,
                prompt_tokens=0 if usage is None else usage.input_tokens,
                completion_tokens=0 if usage is None else usage.output_tokens,
                cost=(
                    0 if usage is None else self.calc_cost_from_response_usage(usage)
                ),
                timestamp=datetime.now(),
            )
        )
        return return_value

    async def embed(
        self,
        request: Request,
        usage_callback: Callable[[APIRequest], Any],
    ) -> CreateEmbeddingResponse:
        """
        Run an embedding request.
        """
        if not "embedding" in self.model.model.type:
            raise HTTPException(404, "This model does not offer non streamed responses")
        request_data = await request.json()
        client: httpx.AsyncClient = request.app.state.httpx_client
        httpx_request = self.build_request(request=request_data, path="/v1/embeddings")
        model_response = await client.send(httpx_request)
        await self.check_response(model_response)
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

# MIT License
#
# Copyright (c) 2023 Andrei Betlen, Thomas Pfau
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from typing import (
    Any,
    Callable,
    Coroutine,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
    Dict,
)
from typing_extensions import TypedDict, Literal, NotRequired
from pydantic import BaseModel, Field

JsonType = Union[None, int, str, bool, List[Any], Dict[str, Any]]


class ChatCompletionRequestMessageContentPartText(TypedDict):
    type: Literal["text"]
    text: str


class ChatCompletionRequestMessageContentPartImageImageUrl(TypedDict):
    url: str
    detail: NotRequired[Literal["auto", "low", "high"]]


class ChatCompletionRequestMessageContentPartImage(TypedDict):
    type: Literal["image_url"]
    image_url: Union[str, ChatCompletionRequestMessageContentPartImageImageUrl]


ChatCompletionRequestMessageContentPart = Union[
    ChatCompletionRequestMessageContentPartText,
    ChatCompletionRequestMessageContentPartImage,
]


class ChatCompletionRequestSystemMessage(TypedDict):
    role: Literal["system"]
    content: Optional[str]


class ChatCompletionRequestUserMessage(TypedDict):
    role: Literal["user"]
    content: Optional[Union[str, List[ChatCompletionRequestMessageContentPart]]]


class ChatCompletionMessageToolCallFunction(TypedDict):
    name: str
    arguments: str


class ChatCompletionMessageToolCall(TypedDict):
    id: str
    type: Literal["function"]
    function: ChatCompletionMessageToolCallFunction


ChatCompletionMessageToolCalls = List[ChatCompletionMessageToolCall]


class ChatCompletionRequestAssistantMessageFunctionCall(TypedDict):
    name: str
    arguments: str


class ChatCompletionRequestAssistantMessage(TypedDict):
    role: Literal["assistant"]
    content: Optional[str]
    tool_calls: NotRequired[ChatCompletionMessageToolCalls]
    function_call: NotRequired[
        ChatCompletionRequestAssistantMessageFunctionCall
    ]  # DEPRECATED


class ChatCompletionRequestToolMessage(TypedDict):
    role: Literal["tool"]
    content: Optional[str]
    tool_call_id: str


class ChatCompletionRequestFunctionMessage(TypedDict):
    role: Literal["function"]
    content: Optional[str]
    name: str


ChatCompletionRequestMessage = Union[
    ChatCompletionRequestSystemMessage,
    ChatCompletionRequestUserMessage,
    ChatCompletionRequestAssistantMessage,
    ChatCompletionRequestUserMessage,
    ChatCompletionRequestToolMessage,
    ChatCompletionRequestFunctionMessage,
]


class ChatCompletionFunction(TypedDict):
    name: str
    description: NotRequired[str]
    parameters: Dict[str, JsonType]  # TODO: make this more specific


class ChatCompletionRequestFunctionCallOption(TypedDict):
    name: str


ChatCompletionRequestFunctionCall = Union[
    Literal["none", "auto"], ChatCompletionRequestFunctionCallOption
]

ChatCompletionFunctionParameters = Dict[str, JsonType]  # TODO: make this more specific


class ChatCompletionToolFunction(TypedDict):
    name: str
    description: NotRequired[str]
    parameters: ChatCompletionFunctionParameters


class ChatCompletionTool(TypedDict):
    type: Literal["function"]
    function: ChatCompletionToolFunction


class ChatCompletionNamedToolChoiceFunction(TypedDict):
    name: str


class ChatCompletionNamedToolChoice(TypedDict):
    type: Literal["function"]
    function: ChatCompletionNamedToolChoiceFunction


ChatCompletionToolChoiceOption = Union[
    Literal["none", "auto"], ChatCompletionNamedToolChoice
]


class ChatCompletionRequestResponseFormat(TypedDict):
    type: Literal["text", "json_object"]

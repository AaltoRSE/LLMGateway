# MIT License
#
# Copyright (c) 2023 Andrei Betlen, Thomas Pfau
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from . import llama_types

from typing import (
    List,
    Optional,
    Union,
    Dict,
    Any,
)
from typing_extensions import Literal
from pydantic import BaseModel, Field


JsonType = Union[None, int, str, bool, List[Any], Dict[str, Any]]

model_field = Field(
    description="The model to use for generating completions.", default="llama2-7b"
)

max_tokens_field = Field(
    default=16, ge=1, description="The maximum number of tokens to generate."
)

temperature_field = Field(
    default=0.8,
    ge=0.0,
    le=2.0,
    description="Adjust the randomness of the generated text.\n\n"
    + "Temperature is a hyperparameter that controls the randomness of the generated text. It affects the probability distribution of the model's output tokens. A higher temperature (e.g., 1.5) makes the output more random and creative, while a lower temperature (e.g., 0.5) makes the output more focused, deterministic, and conservative. The default value is 0.8, which provides a balance between randomness and determinism. At the extreme, a temperature of 0 will always pick the most likely next token, leading to identical outputs in each run.",
)

top_p_field = Field(
    default=0.95,
    ge=0.0,
    le=1.0,
    description="Limit the next token selection to a subset of tokens with a cumulative probability above a threshold P.\n\n"
    + "Top-p sampling, also known as nucleus sampling, is another text generation method that selects the next token from a subset of tokens that together have a cumulative probability of at least p. This method provides a balance between diversity and quality by considering both the probabilities of tokens and the number of tokens to sample from. A higher value for top_p (e.g., 0.95) will lead to more diverse text, while a lower value (e.g., 0.5) will generate more focused and conservative text.",
)

min_p_field = Field(
    default=0.05,
    ge=0.0,
    le=1.0,
    description="Sets a minimum base probability threshold for token selection.\n\n"
    + "The Min-P sampling method was designed as an alternative to Top-P, and aims to ensure a balance of quality and variety. The parameter min_p represents the minimum probability for a token to be considered, relative to the probability of the most likely token. For example, with min_p=0.05 and the most likely token having a probability of 0.9, logits with a value less than 0.045 are filtered out.",
)

stop_field = Field(
    default=None,
    description="A list of tokens at which to stop generation. If None, no stop tokens are used.",
)

stream_field = Field(
    default=False,
    description="Whether to stream the results as they are generated. Useful for chatbots.",
)

top_k_field = Field(
    default=40,
    ge=0,
    description="Limit the next token selection to the K most probable tokens.\n\n"
    + "Top-k sampling is a text generation method that selects the next token only from the top k most likely tokens predicted by the model. It helps reduce the risk of generating low-probability or nonsensical tokens, but it may also limit the diversity of the output. A higher value for top_k (e.g., 100) will consider more tokens and lead to more diverse text, while a lower value (e.g., 10) will focus on the most probable tokens and generate more conservative text.",
)

repeat_penalty_field = Field(
    default=1.1,
    ge=0.0,
    description="A penalty applied to each token that is already generated. This helps prevent the model from repeating itself.\n\n"
    + "Repeat penalty is a hyperparameter used to penalize the repetition of token sequences during text generation. It helps prevent the model from generating repetitive or monotonous text. A higher value (e.g., 1.5) will penalize repetitions more strongly, while a lower value (e.g., 0.9) will be more lenient.",
)

presence_penalty_field = Field(
    default=0.0,
    ge=-2.0,
    le=2.0,
    description="Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.",
)

frequency_penalty_field = Field(
    default=0.0,
    ge=-2.0,
    le=2.0,
    description="Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.",
)

mirostat_mode_field = Field(
    default=0,
    ge=0,
    le=2,
    description="Enable Mirostat constant-perplexity algorithm of the specified version (1 or 2; 0 = disabled)",
)

mirostat_tau_field = Field(
    default=5.0,
    ge=0.0,
    le=10.0,
    description="Mirostat target entropy, i.e. the target perplexity - lower values produce focused and coherent text, larger values produce more diverse and less coherent text",
)

mirostat_eta_field = Field(
    default=0.1, ge=0.001, le=1.0, description="Mirostat learning rate"
)

grammar = Field(
    default=None,
    description="A CBNF grammar (as string) to be used for formatting the model's output.",
)


class CompletionRequest(BaseModel):
    prompt: Union[str, List[str]] = Field(
        default="", description="The prompt to generate completions for."
    )
    suffix: Optional[str] = Field(
        default=None,
        description="A suffix to append to the generated text. If None, no suffix is appended. Useful for chatbots.",
    )
    max_tokens: int = max_tokens_field
    temperature: float = temperature_field
    top_p: float = top_p_field
    min_p: float = min_p_field
    echo: bool = Field(
        default=False,
        description="Whether to echo the prompt in the generated text. Useful for chatbots.",
    )
    stop: Optional[Union[str, List[str]]] = stop_field
    stream: bool = stream_field
    logprobs: Optional[int] = Field(
        default=None,
        ge=0,
        description="The number of logprobs to generate. If None, no logprobs are generated.",
    )
    presence_penalty: Optional[float] = presence_penalty_field
    frequency_penalty: Optional[float] = frequency_penalty_field
    logit_bias: Optional[Dict[str, float]] = Field(None)
    logprobs: Optional[int] = Field(None)
    seed: Optional[int] = Field(None)

    # Will be used to determine the model
    model: Optional[str] = model_field
    # ignored or currently unsupported
    n: Optional[int] = 1
    best_of: Optional[int] = 1
    user: Optional[str] = Field(default=None)

    # llama.cpp specific parameters
    top_k: int = top_k_field
    repeat_penalty: float = repeat_penalty_field
    logit_bias_type: Optional[Literal["input_ids", "tokens"]] = Field(None)
    mirostat_mode: int = mirostat_mode_field
    mirostat_tau: float = mirostat_tau_field
    mirostat_eta: float = mirostat_eta_field
    grammar: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "\n\n### Instructions:\nWhat is the capital of France?\n\n### Response:\n",
                    "stop": ["\n", "###"],
                }
            ]
        }
    }


class ChatCompletionRequestMessage(BaseModel):
    role: Literal["system", "user", "assistant", "function"] = Field(
        default="user", description="The role of the message."
    )
    content: Optional[str] = Field(
        default="", description="The content of the message."
    )


class ChatCompletionRequest(BaseModel):
    messages: List[ChatCompletionRequestMessage] = Field(
        default=[], description="A list of messages to generate completions for."
    )
    functions: Optional[List[llama_types.ChatCompletionFunction]] = Field(
        default=None,
        description="A list of functions to apply to the generated completions.",
    )
    function_call: Optional[llama_types.ChatCompletionRequestFunctionCall] = Field(
        default=None,
        description="A function to apply to the generated completions.",
    )
    tools: Optional[List[llama_types.ChatCompletionTool]] = Field(
        default=None,
        description="A list of tools to apply to the generated completions.",
    )
    tool_choice: Optional[llama_types.ChatCompletionToolChoiceOption] = Field(
        default=None,
        description="A tool to apply to the generated completions.",
    )  # TODO: verify
    max_tokens: Optional[int] = Field(
        default=None,
        description="The maximum number of tokens to generate. Defaults to inf",
    )
    temperature: float = temperature_field
    top_p: float = top_p_field
    min_p: float = min_p_field
    stop: Optional[Union[str, List[str]]] = stop_field
    stream: bool = stream_field
    presence_penalty: Optional[float] = presence_penalty_field
    frequency_penalty: Optional[float] = frequency_penalty_field
    logit_bias: Optional[Dict[str, float]] = Field(None)
    seed: Optional[int] = Field(None)
    response_format: Optional[llama_types.ChatCompletionRequestResponseFormat] = Field(
        default=None,
    )

    # ignored or currently unsupported
    model: Optional[str] = model_field
    n: Optional[int] = 1
    user: Optional[str] = Field(None)

    # llama.cpp specific parameters
    top_k: int = top_k_field
    repeat_penalty: float = repeat_penalty_field
    logit_bias_type: Optional[Literal["input_ids", "tokens"]] = Field(None)
    mirostat_mode: int = mirostat_mode_field
    mirostat_tau: float = mirostat_tau_field
    mirostat_eta: float = mirostat_eta_field
    grammar: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "messages": [
                        ChatCompletionRequestMessage(
                            role="system", content="You are a helpful assistant."
                        ).model_dump(),
                        ChatCompletionRequestMessage(
                            role="user", content="What is the capital of France?"
                        ).model_dump(),
                    ]
                }
            ]
        }
    }


class EmbeddingRequest(BaseModel):
    model: Optional[str] = model_field
    input: Union[str, List[str]] = Field(description="The input to embed.")
    user: Optional[str] = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "input": "The food was delicious and the waiter...",
                }
            ]
        }
    }

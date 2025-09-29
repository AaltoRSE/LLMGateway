"""
Utility functions for stream response processing
"""

import logging
from typing import Tuple

# from .requests import ChatCompletionRequest
import re
import json


from app.schemas.openai_schemas import CompletionUsage, ResponseUsage, Response1

logger = logging.getLogger("app")


def process_completion_stream(
    stream_chunk: str,
) -> Tuple[CompletionUsage | None, str | None]:
    """
    Function to process a completion stream chunk, returning usage, if it's there
    """
    data_match = re.search(r"^data\s*:\s*(.*)", stream_chunk, re.MULTILINE)
    data = None
    if data_match:
        data = data_match.group(1)
    usage_info = None
    try:
        if data:
            if data.strip() == "[DONE]":
                pass
            else:
                parsed_json = json.loads(data)
                # choices has to be empty in the usage chunk. This ensures,
                # that this works with kubeai/openwebui
                if "usage" in parsed_json and len(parsed_json["choices"]) == 0:
                    usage_info = CompletionUsage.model_validate(parsed_json["usage"])
                # dataChoices = parsed_json["choices"]
                # completion_tokens = completion_tokens + len(dataChoices)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # FIXME This needs proper logging to see if there are some errors
        logger.warning("Issue in processing tokens")
        logger.warning(e)
    return usage_info, data


def process_response_stream(
    stream_chunk: str,
) -> Tuple[ResponseUsage | None, str | None, str | None]:
    """
    Function to process a response stream chunk, returning usage, if it's there
    """
    usage_info = None
    event = None
    # Extract event line
    event_match = re.search(r"^event\s*:\s*(\S+)", stream_chunk, re.MULTILINE)
    data_match = re.search(r"^data\s*:\s*(.*)", stream_chunk, re.MULTILINE)
    data = None
    if data_match:
        data = data_match.group(1)
    if event_match:
        event = event_match.group(1)
    if event != "response.completed":
        return usage_info, event, data

    try:
        if data_match:
            parsed_json = json.loads(data_match.group(1))
            response = Response1.model_validate(parsed_json["response"])
            usage_info = response.usage
            # dataChoices = parsed_json["choices"]
            # completion_tokens = completion_tokens + len(dataChoices)
        else:
            logger.warning("Got response completed but no data.")
    except json.JSONDecodeError as e:
        logger.warning("Issue in processing tokens")
        logger.warning(e)

    return usage_info, event, data

from app.utils.logging_handler import LoggingHandler
from app.services.quota_service import QuotaService
from app.models.keys import UserKey
from app.models.model import LLMModel
from app.models.quota import RequestTokens, RequestQuota
import logging

# from .requests import ChatCompletionRequest
import re
import json

logger = logging.getLogger("app")


def getTokensForChunk(streamChunk: str):
    regex = "(?:^data: )(.*)"
    matches = re.findall(regex, streamChunk)
    prompt_tokens = 0
    completion_tokens = 0
    for tokens in matches:
        if tokens.strip() == "[DONE]":
            pass
        else:
            parsed_json = json.loads(tokens)
            logger.info(parsed_json)
            # dataChoices = parsed_json["choices"]
            # completion_tokens = completion_tokens + len(dataChoices)

    return RequestTokens(
        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
    )


class StreamLogger:
    def __init__(self, quota_service: QuotaService, source: UserKey, model: LLMModel):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.quota_service = quota_service
        self.model = model
        self.source = source

    #    def log_request(self, requestData: ChatCompletionRequest):
    # Not implemented for now, will come later but needs model specific
    # Token calculation
    #        pass

    def handle_chunk(self, chunk: str):
        """
        This function handles a chunk of data from the stream
        It will return that this was the usage stream.
        """
        chunk_tokens = getTokensForChunk(chunk)
        if chunk_tokens.prompt_tokens > 0 or chunk_tokens.completion_tokens > 0:
            request_quota = RequestQuota(
                prompt_tokens=chunk_tokens.prompt_tokens,
                completion_tokens=chunk_tokens.completion_tokens,
                prompt_cost=self.model.prompt_cost,
                completion_cost=self.model.completion_cost,
            )
            self.quota_service.update_quota(
                self.source, self.model.model.id, request_quota
            )
            return False
        return True

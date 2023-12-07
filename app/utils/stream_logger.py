from .logging_handler import LoggingHandler

# from .requests import ChatCompletionRequest
import re
import json


def getTokensForChunk(streamChunk: str):
    regex = "(?:^data: )(.*)"
    matches = re.findall(regex, streamChunk)
    tokenCount = 0
    for tokens in matches:
        if tokens.strip() == "[DONE]":
            pass
        else:
            parsed_json = json.loads(tokens)
            dataChoices = parsed_json["choices"]
            tokenCount = tokenCount + len(dataChoices)

    return tokenCount


class StreamLogger:
    def __init__(
        self, logging_handler: LoggingHandler, source: str, iskey: bool, model: str
    ):
        self.tokenCount = 0
        self.logger = logging_handler
        self.model = model
        self.source = source
        self.iskey = iskey

    #    def log_request(self, requestData: ChatCompletionRequest):
    # Not implemented for now, will come later but needs model specific
    # Token calculation
    #        pass

    def handle_chunk(self, chunk: str):
        self.tokenCount = self.tokenCount + getTokensForChunk(chunk)

    def finish(self):
        if self.iskey:
            self.logger.log_usage_for_key(
                tokencount=self.tokenCount, model=self.model, key=self.source
            )
        else:
            self.logger.log_usage_for_user(
                tokencount=self.tokenCount, model=self.model, user=self.source
            )

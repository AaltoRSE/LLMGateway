from .logging_handler import LoggingHandler
from typing import AsyncIterator
import logging

debug_logger = logging.getLogger("app")

# from .requests import ChatCompletionRequest
import re
import json


class StreamLogger:
    def __init__(
        self,
        logging_handler: LoggingHandler,
        source: str,
        iskey: bool,
        model: str,
        stream: AsyncIterator[str],
        request_usage_added: bool = False,
    ):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.logger = logging_handler
        self.model = model
        self.source = source
        self.iskey = iskey
        self.stream = stream
        self.request_usage_added = request_usage_added

    #    def log_request(self, requestData: ChatCompletionRequest):
    # Not implemented for now, will come later but needs model specific
    # Token calculation
    #        pass
    def handle_chunk(self, chunk: str):
        debug_logger.info(chunk)
        regex = "(?:^data: )(.*)"
        matches = re.findall(regex, chunk)
        for tokens in matches:
            if tokens.strip() == "[DONE]":
                pass
            else:
                parsed_json = json.loads(tokens)
                # Need to check, what exactly is being sent here from the model in the end
                if "usage" in parsed_json:
                    if parsed_json["usage"] != None:
                        # We will set them here, as anything before is not relevant
                        self.prompt_tokens = parsed_json["usage"]["prompt_tokens"]
                        self.completion_tokens = parsed_json["usage"][
                            "completion_tokens"
                        ]
                    if self.request_usage_added:
                        # Remove the usage part from the response
                        parsed_json.pop("usage")
                        # re-encode the tokens. This is a bit hacky, but should work for now.
                        # only ever replace one occurence...
                        chunk = chunk.replace(tokens, json.dumps(parsed_json), count=1)
                else:
                    dataChoices = parsed_json["choices"]
                    self.completion_tokens = self.completion_tokens + len(dataChoices)
        return chunk

    async def process(self):
        async for chunk in self.stream:
            yield self.handle_chunk(chunk)

    def finish(self):
        if self.iskey:
            self.logger.log_usage_for_key(
                token_count=self.completion_tokens, model=self.model, key=self.source
            )
            self.logger.log_usage_for_key(
                token_count=self.prompt_tokens,
                model=self.model,
                key=self.source,
                prompt=True,
            )
        else:
            self.logger.log_usage_for_user(
                token_count=self.completion_tokens, model=self.model, user=self.source
            )
            self.logger.log_usage_for_user(
                token_count=self.prompt_tokens,
                model=self.model,
                user=self.source,
                prompt=True,
            )

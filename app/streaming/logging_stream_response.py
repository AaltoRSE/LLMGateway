from fastapi.responses import StreamingResponse
from server_logging.stream_logger import StreamLogger


async def forward_stream(logger: StreamLogger, input_stream):
    # Walk through all chunks and forward them, while passing them through the logger.
    async for chunk in input_stream:
        logger.debug(chunk)
        yield chunk
    logger.finish()


class LoggingStreamingResponse(StreamingResponse):
    def __init__(self, logger: StreamLogger, input_stream):
        super().__init__(forward_stream(logger, input_stream))

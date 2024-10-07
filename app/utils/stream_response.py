from starlette.responses import StreamingResponse
import anyio
from starlette.types import Send
from app.utils.stream_logger import StreamLogger
import logging

logger = logging.getLogger("app")


class LoggingStreamResponse(StreamingResponse):
    def __init__(self, streamlogger: StreamLogger, include_usage: bool, **kwargs):
        super().__init__(**kwargs)
        self.streamlogger = streamlogger
        self.include_usage = include_usage

    async def stream_response(self, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )
        logger.info(self.include_usage)
        async for chunk in self.body_iterator:
            if not isinstance(chunk, (bytes, memoryview)):
                usage_chunk = self.streamlogger.handle_chunk(chunk)
                chunk = chunk.encode(self.charset)
            else:
                usage_chunk = self.streamlogger.handle_chunk(chunk.decode())
            # Only pass on the usage if it was requested.
            logger.info(usage_chunk)
            logger.info(chunk)

            if not usage_chunk or self.include_usage:
                await send(
                    {"type": "http.response.body", "body": chunk, "more_body": True}
                )

        await send({"type": "http.response.body", "body": b"", "more_body": False})

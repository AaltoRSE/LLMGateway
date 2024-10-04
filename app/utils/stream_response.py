from starlette.responses import StreamingResponse
import anyio
from starlette.types import Send
from app.utils.stream_logger import StreamLogger


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
        async for chunk in self.body_iterator:
            if not isinstance(chunk, (bytes, memoryview)):
                chunk = chunk.encode(self.charset)
            usage_chunk = self.streamlogger.handle_chunk(chunk)
            # Only pass on the usage if it was requested.
            if not usage_chunk or self.include_usage:
                await send(
                    {"type": "http.response.body", "body": chunk, "more_body": True}
                )

        await send({"type": "http.response.body", "body": b"", "more_body": False})

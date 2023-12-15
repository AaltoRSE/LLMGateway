from fastapi.responses import StreamingResponse
import typing

from .stream_logger import StreamLogger

from starlette.types import Send
from sse_starlette.sse import EventSourceResponse
from sse_starlette.sse import ServerSentEvent


def ensure_bytes(
    data: typing.Union[bytes, dict, ServerSentEvent, typing.Any], sep: str
) -> bytes:
    if isinstance(data, bytes):
        return data
    elif isinstance(data, ServerSentEvent):
        return data.encode()
    elif isinstance(data, dict):
        data["sep"] = sep
        return ServerSentEvent(**data).encode()
    else:
        return ServerSentEvent(str(data), sep=sep).encode()


Content = typing.Union[str, bytes, dict, ServerSentEvent]
SyncContentStream = typing.Iterator[Content]
AsyncContentStream = typing.AsyncIterable[Content]
ContentStream = typing.Union[AsyncContentStream, SyncContentStream]


async def event_generator(iterator: typing.AsyncIterator[bytes]) -> ContentStream:
    async for chunk in iterator:
        yield chunk


class LoggingStreamResponse(EventSourceResponse):
    def __init__(self, logger: StreamLogger, **kwargs) -> None:
        super().__init__(**kwargs)
        self.logger = logger

    async def stream_response(self, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )
        async for data in self.body_iterator:
            chunk = ensure_bytes(data, self.sep)
            self.logger.handle_chunk(chunk.decode())
            await send({"type": "http.response.body", "body": chunk, "more_body": True})

        async with self._send_lock:
            self.active = False
            self.logger.finish()
            await send({"type": "http.response.body", "body": b"", "more_body": False})

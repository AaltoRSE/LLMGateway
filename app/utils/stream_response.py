from sse_starlette.sse import EventSourceResponse, ensure_bytes, SendTimeoutError
import anyio
from starlette.responses import ContentStream
from starlette.types import Send
from app.utils.stream_logger import StreamLogger
from typing import AsyncIterator

import logging

logger = logging.getLogger("app")


async def event_generator(iterator: AsyncIterator[bytes]) -> ContentStream:
    async for chunk in iterator:
        yield chunk


class LoggingStreamResponse(EventSourceResponse):
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
        logger.info("Running stream response")
        logger.info(self.body_iterator)
        async for data in self.body_iterator:
            chunk = ensure_bytes(data, self.sep)
            logger.debug("chunk: %s", chunk)
            usage_chunk = self.streamlogger.handle_chunk(chunk.decode())
            if not usage_chunk or self.include_usage:
                with anyio.move_on_after(self.send_timeout) as timeout:
                    await send(
                        {"type": "http.response.body", "body": chunk, "more_body": True}
                    )
                if timeout.cancel_called:
                    if hasattr(self.body_iterator, "aclose"):
                        await self.body_iterator.aclose()
                    raise SendTimeoutError()
        logger.info("!iterator done")
        async with self._send_lock:
            self.active = False
            await send({"type": "http.response.body", "body": b"", "more_body": False})

        # await send(
        #     {
        #         "type": "http.response.start",
        #         "status": self.status_code,
        #         "headers": self.raw_headers,
        #     }
        # )
        # logger.info(self.include_usage)
        # async for chunk in self.body_iterator:
        #     if not isinstance(chunk, (bytes, memoryview)):
        #         usage_chunk = self.streamlogger.handle_chunk(chunk)
        #         chunk = chunk.encode(self.charset)
        #     else:
        #         usage_chunk = self.streamlogger.handle_chunk(chunk.decode())
        #     # Only pass on the usage if it was requested.
        #     logger.info(usage_chunk)
        #     logger.info(chunk)

        #     if not usage_chunk or self.include_usage:
        #         await send(
        #             {"type": "http.response.body", "body": chunk, "more_body": True}
        #         )

        # await send({"type": "http.response.body", "body": b"", "more_body": False})

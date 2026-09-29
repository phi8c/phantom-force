from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from shared.messaging.contracts import MessageConsumer, ReceivedMessage


logger = logging.getLogger(__name__)


class RabbitMQReceivedMessage(ReceivedMessage):
    def __init__(self, raw_message: Any, *, queue_name: str | None = None) -> None:
        self._raw_message = raw_message
        self._queue_name = queue_name
        self._payload: dict[str, Any] | None = None

    @property
    def payload(self) -> dict[str, Any]:
        if self._payload is None:
            self._payload = self._parse_payload(self._raw_message.body)
        return self._payload

    async def ack(self) -> None:
        await self._raw_message.ack()
        logger.info(
            "rabbitmq acknowledged queue=%s job_id=%s",
            self._queue_name,
            (
                self._payload.get("ingestion_job_id")
                if self._payload is not None
                else None
            ),
        )

    async def nack(self, *, requeue: bool = True) -> None:
        await self._raw_message.nack(requeue=requeue)
        logger.warning(
            "rabbitmq rejected queue=%s job_id=%s requeue=%s",
            self._queue_name,
            (
                self._payload.get("ingestion_job_id")
                if self._payload is not None
                else None
            ),
            requeue,
        )

    @staticmethod
    def _parse_payload(body: bytes) -> dict[str, Any]:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("RabbitMQ message contains invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("RabbitMQ message payload must be a JSON object.")
        return payload


class RabbitMQMessageConsumer(MessageConsumer):
    def __init__(self, queue: Any, *, queue_name: str | None = None) -> None:
        self._queue = queue
        self._queue_name = queue_name
        self._messages: asyncio.Queue[Any] = asyncio.Queue()
        self._start_lock = asyncio.Lock()
        self._consumer_tag: str | None = None
        self._closed = False

    async def start(self) -> None:
        if self._consumer_tag is not None:
            return
        async with self._start_lock:
            if self._consumer_tag is not None:
                return
            if self._closed:
                raise RuntimeError("RabbitMQ consumer is closed.")
            self._consumer_tag = await self._queue.consume(
                self._on_message,
                no_ack=False,
            )
            logger.info(
                "rabbitmq consumer_registered queue=%s consumer_tag=%s",
                self._queue_name,
                self._consumer_tag,
            )

    async def close(self) -> None:
        async with self._start_lock:
            if self._closed:
                return
            self._closed = True
            consumer_tag = self._consumer_tag
            self._consumer_tag = None

            if consumer_tag is None or not self._channel_is_usable():
                return

            await self._queue.cancel(consumer_tag)
            logger.info(
                "rabbitmq consumer_cancelled queue=%s consumer_tag=%s",
                self._queue_name,
                consumer_tag,
            )

    async def receive(
        self,
        *,
        max_messages: int = 1,
        wait_timeout: float = 5,
    ) -> list[ReceivedMessage]:
        if max_messages <= 0:
            raise ValueError("max_messages must be greater than 0.")
        if wait_timeout < 0:
            raise ValueError("wait_timeout cannot be negative.")
        if self._closed:
            raise RuntimeError("RabbitMQ consumer is closed.")

        await self.start()

        loop = asyncio.get_running_loop()
        deadline = loop.time() + wait_timeout
        received: list[ReceivedMessage] = []

        while len(received) < max_messages:
            remaining = max(0.0, deadline - loop.time())
            try:
                if remaining <= 0:
                    raw_message = self._messages.get_nowait()
                else:
                    raw_message = await asyncio.wait_for(
                        self._messages.get(),
                        timeout=remaining,
                    )
            except (asyncio.TimeoutError, asyncio.QueueEmpty):
                break

            received.append(
                RabbitMQReceivedMessage(
                    raw_message,
                    queue_name=self._queue_name,
                )
            )

            while len(received) < max_messages:
                try:
                    raw_message = self._messages.get_nowait()
                except asyncio.QueueEmpty:
                    break
                received.append(
                    RabbitMQReceivedMessage(
                        raw_message,
                        queue_name=self._queue_name,
                    )
                )

        if received:
            logger.info(
                "rabbitmq received queue=%s count=%s",
                self._queue_name,
                len(received),
            )
        return received

    async def _on_message(self, raw_message: Any) -> None:
        await self._messages.put(raw_message)

    def _channel_is_usable(self) -> bool:
        channel = getattr(self._queue, "channel", None)
        return channel is None or not getattr(channel, "is_closed", False)

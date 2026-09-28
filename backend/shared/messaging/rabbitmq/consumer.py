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
    EMPTY_QUEUE_POLL_INTERVAL = 0.1

    def __init__(self, queue: Any, *, queue_name: str | None = None) -> None:
        self._queue = queue
        self._queue_name = queue_name

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

        loop = asyncio.get_running_loop()
        deadline = loop.time() + wait_timeout
        received: list[ReceivedMessage] = []

        while len(received) < max_messages:
            remaining = max(0.0, deadline - loop.time())
            if received and remaining <= 0:
                break
            raw_message = await self._queue.get(
                no_ack=False,
                fail=False,
                timeout=remaining,
            )
            if raw_message is None:
                remaining = max(0.0, deadline - loop.time())
                if remaining <= 0:
                    break
                await asyncio.sleep(
                    min(self.EMPTY_QUEUE_POLL_INTERVAL, remaining)
                )
                continue
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

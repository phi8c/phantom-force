from __future__ import annotations

import asyncio
import json
from typing import Any

import aio_pika


class RabbitMQPublisher:
    def __init__(self, channel: Any) -> None:
        self._channel = channel
        self._declared_queues: set[str] = set()
        self._declaration_lock = asyncio.Lock()

    async def publish(
        self,
        queue_name: str,
        payload: dict[str, Any],
    ) -> None:
        if not queue_name.strip():
            raise ValueError("RabbitMQ queue name cannot be empty.")
        await self._declare_queue(queue_name)
        body = json.dumps(payload).encode("utf-8")
        await self._channel.default_exchange.publish(
            aio_pika.Message(
                body=body,
                content_type="application/json",
                content_encoding="utf-8",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )

    async def _declare_queue(self, queue_name: str) -> None:
        if queue_name in self._declared_queues:
            return
        async with self._declaration_lock:
            if queue_name in self._declared_queues:
                return
            await self._channel.declare_queue(
                queue_name,
                durable=True,
                auto_delete=False,
                exclusive=False,
            )
            self._declared_queues.add(queue_name)

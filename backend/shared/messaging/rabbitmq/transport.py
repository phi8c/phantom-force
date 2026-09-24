from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import aio_pika

from .consumer import RabbitMQMessageConsumer
from .publisher import RabbitMQPublisher


ConnectFunction = Callable[..., Awaitable[Any]]


class RabbitMQTransport:
    """Owns one robust connection and the channels created for queue consumers."""

    def __init__(
        self,
        url: str,
        *,
        connect: ConnectFunction = aio_pika.connect_robust,
        connection_timeout: float = 30,
    ) -> None:
        if not url.strip():
            raise ValueError("RABBITMQ_URL is required.")
        self._url = url
        self._connect = connect
        self._connection_timeout = connection_timeout
        self._connection: Any | None = None
        self._channels: list[Any] = []
        self._connection_lock = asyncio.Lock()

    async def create_consumer(
        self,
        queue_name: str,
        *,
        prefetch_count: int = 1,
    ) -> RabbitMQMessageConsumer:
        if not queue_name.strip():
            raise ValueError("RabbitMQ queue name cannot be empty.")
        if prefetch_count <= 0:
            raise ValueError("RabbitMQ prefetch_count must be greater than 0.")

        connection = await self._get_connection()
        channel = await connection.channel()
        try:
            await channel.set_qos(prefetch_count=prefetch_count)
            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                auto_delete=False,
                exclusive=False,
            )
        except Exception:
            await channel.close()
            raise

        self._channels.append(channel)
        return RabbitMQMessageConsumer(queue)

    async def create_publisher(self) -> RabbitMQPublisher:
        connection = await self._get_connection()
        channel = await connection.channel()
        self._channels.append(channel)
        return RabbitMQPublisher(channel)

    async def close(self) -> None:
        for channel in reversed(self._channels):
            if not getattr(channel, "is_closed", False):
                await channel.close()
        self._channels.clear()

        if self._connection is not None:
            if not getattr(self._connection, "is_closed", False):
                await self._connection.close()
            self._connection = None

    async def _get_connection(self) -> Any:
        if self._connection is not None and not getattr(
            self._connection,
            "is_closed",
            False,
        ):
            return self._connection

        async with self._connection_lock:
            if self._connection is None or getattr(
                self._connection,
                "is_closed",
                False,
            ):
                self._connection = await self._connect(
                    self._url,
                    timeout=self._connection_timeout,
                )
            return self._connection

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aio_pika

from .consumer import RabbitMQMessageConsumer
from .publisher import RabbitMQPublisher


ConnectFunction = Callable[..., Awaitable[Any]]
logger = logging.getLogger(__name__)


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
        self._consumers: list[RabbitMQMessageConsumer] = []
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
            logger.exception(
                "rabbitmq consumer_create_failed queue=%s",
                queue_name,
            )
            await channel.close()
            raise

        consumer = RabbitMQMessageConsumer(queue, queue_name=queue_name)
        try:
            await consumer.start()
        except Exception:
            logger.exception(
                "rabbitmq consumer_register_failed queue=%s",
                queue_name,
            )
            await channel.close()
            raise

        self._channels.append(channel)
        self._consumers.append(consumer)
        logger.info(
            "rabbitmq consumer_ready queue=%s prefetch_count=%s",
            queue_name,
            prefetch_count,
        )
        return consumer

    async def create_publisher(self) -> RabbitMQPublisher:
        connection = await self._get_connection()
        channel = await connection.channel()
        self._channels.append(channel)
        logger.info("rabbitmq publisher_ready")
        return RabbitMQPublisher(channel)

    async def close(self) -> None:
        logger.info(
            "rabbitmq transport_closing channels=%s",
            len(self._channels),
        )
        first_error: BaseException | None = None
        for consumer in reversed(self._consumers):
            try:
                await consumer.close()
            except BaseException as exc:
                logger.exception("rabbitmq consumer_close_failed")
                if first_error is None:
                    first_error = exc
        self._consumers.clear()

        for channel in reversed(self._channels):
            if not getattr(channel, "is_closed", False):
                try:
                    await channel.close()
                except BaseException as exc:
                    if first_error is None:
                        first_error = exc
        self._channels.clear()

        if self._connection is not None:
            if not getattr(self._connection, "is_closed", False):
                try:
                    await self._connection.close()
                except BaseException as exc:
                    if first_error is None:
                        first_error = exc
            self._connection = None
        logger.info("rabbitmq transport_closed")
        if first_error is not None:
            raise first_error

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
                logger.info("rabbitmq connecting")
                try:
                    self._connection = await self._connect(
                        self._url,
                        timeout=self._connection_timeout,
                    )
                except Exception:
                    logger.exception("rabbitmq connection_failed")
                    raise
                logger.info("rabbitmq connected")
            return self._connection

from __future__ import annotations

import json
from abc import ABC
from abc import abstractmethod

from azure.servicebus import ServiceBusReceivedMessage
from azure.servicebus.aio import (
    ServiceBusClient,
    ServiceBusReceiver,
)

from app.application.commands.base_command import BaseCommand
from app.shared.logging.logger import logger

from app.infrastructure.messaging.command_registry import (
    COMMAND_REGISTRY,
)


class BaseConsumer(ABC):

    def __init__(
        self,
        connection_string: str,
        queue_name: str,
    ) -> None:

        self._client = ServiceBusClient.from_connection_string(
            conn_str=connection_string,
        )

        self._queue_name = queue_name

    async def start(self) -> None:
        """
        Start listening messages from Azure Service Bus Queue.
        """

        logger.info(
            "Starting consumer for queue '%s'",
            self._queue_name,
        )

        async with self._client:

            receiver = self._client.get_queue_receiver(
                queue_name=self._queue_name,
            )

            async with receiver:

                async for message in receiver:

                    await self._process_message(
                        receiver,
                        message,
                    )

    async def _process_message(
        self,
        receiver: ServiceBusReceiver,
        message: ServiceBusReceivedMessage,
    ) -> None:

        try:

            logger.info(
                "Received message from queue '%s'",
                self._queue_name,
            )

            body = b"".join(message.body)

            payload = json.loads(
                body.decode("utf-8"),
            )

            command = self._deserialize_command(
    payload,
)

            await self.handle(
                command,
            )

            await receiver.complete_message(
                message,
            )

            logger.info(
                "Message completed successfully.",
            )

        except Exception:

            logger.exception(
                "Failed processing message from queue '%s'",
                self._queue_name,
            )

            await receiver.abandon_message(
                message,
            )

            raise

   
    @abstractmethod
    async def handle(
        self,
        command: BaseCommand,
    ) -> None:
        """
        Execute business logic.
        """
        ...
        
    def _deserialize_command(
        self,
        payload: dict,
    ) -> BaseCommand:

        command_type = payload["command_type"]

        command_data = payload["command"]

        command_cls = COMMAND_REGISTRY.get(
            command_type,
        )

        if command_cls is None:

            raise ValueError(
                f"Unknown command type: {command_type}",
            )

        return command_cls(
            **command_data,
        )
import json
from dataclasses import asdict
from uuid import UUID

from azure.servicebus import ServiceBusClient
from azure.servicebus import ServiceBusMessage

from app.application.commands.base_command import BaseCommand
from app.application.orchestration.contracts.command_bus import CommandBus
from app.infrastructure.messaging.command_bus.queue_mapping import (
    QUEUE_MAPPING,
)
from app.shared.logging.logger import logger


class AzureCommandBus(CommandBus):
    """
    Azure Service Bus implementation of CommandBus.

    Responsibility:
    - Serialize command
    - Resolve destination queue
    - Publish command to Azure Service Bus Queue

    This class DOES NOT:
    - Execute business logic
    - Deserialize commands
    - Retry commands
    - Handle workers
    """

    def __init__(
        self,
        connection_string: str,
    ) -> None:
        self._client = ServiceBusClient.from_connection_string(
            conn_str=connection_string,
            logging_enable=False,
        )

    async def publish(
        self,
        command: BaseCommand,
    ) -> None:
        """
        Publish a command to Azure Service Bus Queue.
        """

        queue_name = QUEUE_MAPPING.get(type(command))

        if queue_name is None:
            raise ValueError(
                f"No queue mapping found for command "
                f"{type(command).__name__}"
            )

        payload = {
            "command_type": command.__class__.__name__,
            "command": self._serialize(command),
        }

        message = ServiceBusMessage(
            body=json.dumps(payload)
        )

        logger.info(
            "Publishing command '%s' to queue '%s'",
            command.__class__.__name__,
            queue_name,
        )

        async with self._client:

            sender = self._client.get_queue_sender(
                queue_name=queue_name,
            )

            async with sender:
                await sender.send_messages(message)

        logger.info(
            "Published command '%s' successfully",
            command.__class__.__name__,
        )

    @staticmethod
    def _serialize(
        command: BaseCommand,
    ) -> dict:
        """
        Convert dataclass command to JSON serializable dict.
        """

        data = asdict(command)

        for key, value in data.items():

            if isinstance(value, UUID):
                data[key] = str(value)

        return data
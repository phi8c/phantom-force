import json

from azure.servicebus import (
    ServiceBusMessage,
)

from azure.servicebus.aio import (
    ServiceBusClient,
)

from app.domain.enums.task_type import (
    TaskType,
)

from app.domain.ports.messaging.message_bus import (
    MessageBus,
)

from app.shared.config.settings import (
    settings,
)


class AzureServiceBus(
    MessageBus,
):

    QUEUE_MAPPING = {
        TaskType.DOWNLOAD:
            settings.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE,

        TaskType.EXTRACT:
            settings.AZURE_SERVICE_BUS_EXTRACT_QUEUE,

        TaskType.CHUNK:
            settings.AZURE_SERVICE_BUS_CHUNK_QUEUE,

        TaskType.EMBED:
            settings.AZURE_SERVICE_BUS_EMBED_QUEUE,

        TaskType.CLASSIFY:
            settings.AZURE_SERVICE_BUS_CLASSIFY_QUEUE,

        TaskType.INDEX:
            settings.AZURE_SERVICE_BUS_INDEX_QUEUE,
    }

    def __init__(
        self,
    ):
        self.connection_string = (
            settings.AZURE_SERVICE_BUS_CONNECTION_STRING
        )

    async def _publish(
        self,
        queue_name: str,
        task_id: str,
        task_type: str,
    ):

        payload = {
            "task_id": task_id,
            "task_type": task_type,
        }

        client = (
            ServiceBusClient
            .from_connection_string(
                self.connection_string,
            )
        )

        async with client:

            sender = (
                client.get_queue_sender(
                    queue_name=queue_name,
                )
            )

            async with sender:

                await sender.send_messages(
                    ServiceBusMessage(
                        json.dumps(
                            payload,
                        )
                    )
                )

    async def publish_task(
        self,
        task_id: str,
        task_type: str,
    ):

        queue_name = (
            self.QUEUE_MAPPING[
                task_type
            ]
        )

        await self._publish(
            queue_name=queue_name,
            task_id=task_id,
            task_type=task_type,
        )
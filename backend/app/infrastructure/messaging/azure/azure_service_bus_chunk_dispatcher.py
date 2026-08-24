import json

from azure.servicebus import (
    ServiceBusMessage,
)
from azure.servicebus.aio import (
    ServiceBusClient,
)

from app.application.ingestion.messages.chunk_message import (
    ChunkMessage,
)


class AzureServiceBusChunkDispatcher:

    def __init__(
        self,
        connection_string: str,
        queue_name: str,
    ):
        self.connection_string = (
            connection_string
        )

        self.queue_name = (
            queue_name
        )

    async def dispatch(
        self,
        message: ChunkMessage,
    ) -> None:

        payload = {
            "document_id": str(
                message.document_id,
            ),
            "extraction_id": str(
                message.extraction_id,
            ),
        }

        client = (
            ServiceBusClient.from_connection_string(
                self.connection_string,
            )
        )

        async with client:

            sender = (
                client.get_queue_sender(
                    queue_name=self.queue_name,
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
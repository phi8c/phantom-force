import json
from uuid import UUID

from azure.servicebus import ServiceBusMessage

from module.ingest.embedding.domain.contracts.embedding_dispatcher import (
    EmbeddingDispatcher,
)


class AzureEmbeddingDispatcher(
    EmbeddingDispatcher,
):

    def __init__(
        self,
        service_bus_client,
        queue_name: str,
    ):
        self.service_bus_client = service_bus_client
        self.queue_name = queue_name

    async def dispatch_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:

        payload = {
            "ingestion_job_id": str(
                ingestion_job_id
            ),
        }

        sender = self.service_bus_client.get_queue_sender(
            queue_name=self.queue_name,
        )

        async with sender:
            await sender.send_messages(
                ServiceBusMessage(
                    json.dumps(payload),
                )
            )

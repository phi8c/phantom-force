import json
from uuid import UUID

from azure.storage.queue.aio import QueueClient

from module.ingest.discovery.domain.contracts.discovery_dispatcher import (
    DiscoveryDispatcher,
)


class AzureDiscoveryDispatcher(
    DiscoveryDispatcher,
):

    def __init__(
        self,
        queue_client: QueueClient,
    ):
        self.queue_client = queue_client

    async def dispatch(
        self,
        ingestion_job_id: UUID,
        batch_size: int,
    ) -> None:

        payload = {
            "ingestion_job_id": str(
                ingestion_job_id
            ),
            "batch_size": batch_size,
        }

        await self.queue_client.send_message(
            json.dumps(payload)
        )
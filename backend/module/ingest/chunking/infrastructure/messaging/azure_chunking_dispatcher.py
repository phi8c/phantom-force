import json
from uuid import UUID

from azure.storage.queue.aio import QueueClient

from module.ingest.chunking.domain.contracts.chunking_dispatcher import (
    ChunkingDispatcher,
)


class AzureChunkingDispatcher(
    ChunkingDispatcher,
):

    def __init__(
        self,
        queue_client: QueueClient,
    ):
        self.queue_client = queue_client

    async def dispatch(
        self,
        ingestion_job_id: UUID,
    ) -> None:

        payload = {
            "ingestion_job_id": str(
                ingestion_job_id
            ),
        }

        await self.queue_client.send_message(
            json.dumps(payload)
        )

import json
from uuid import UUID

from module.ingest.download.domain.contracts.download_dispatcher import (
    DownloadDispatcher,
)


class AzureDownloadDispatcher(
    DownloadDispatcher,
):

    def __init__(
        self,
        queue_client,
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

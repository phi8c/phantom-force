import json
from uuid import UUID

from module.ingest.extraction.domain.contracts.extraction_dispatcher import (
    ExtractionDispatcher,
)


class AzureExtractionDispatcher(
    ExtractionDispatcher,
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

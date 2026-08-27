import json
from uuid import UUID

from module.ingest.classification.domain.contracts.classification_dispatcher import (
    ClassificationDispatcher,
)


class AzureClassificationDispatcher(
    ClassificationDispatcher,
):

    def __init__(
        self,
        queue_client,
    ):
        self.queue_client = queue_client

    async def dispatch_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:

        await self.queue_client.send_message(
            json.dumps(
                {
                    "ingestion_job_id": str(
                        ingestion_job_id,
                    ),
                }
            )
        )

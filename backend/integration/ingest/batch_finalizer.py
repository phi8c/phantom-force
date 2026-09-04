from uuid import UUID

from module.ingest.chunking.composition import (
    BatchCompletionResult,
    ChunkBatchCompletionService,
)


class IngestBatchFinalizer:

    def __init__(
        self,
        completion_service: ChunkBatchCompletionService,
    ):
        self.completion_service = completion_service

    async def complete_embedding(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
    ) -> BatchCompletionResult:

        return await self.completion_service.complete_embedding(
            ingestion_job_id=ingestion_job_id,
            batch_id=batch_id,
        )

    async def complete_classification(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
    ) -> BatchCompletionResult:

        return await (
            self.completion_service
            .complete_classification(
                ingestion_job_id=ingestion_job_id,
                batch_id=batch_id,
            )
        )

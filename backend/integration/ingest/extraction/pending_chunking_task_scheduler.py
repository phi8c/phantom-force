from uuid import UUID

from module.ingest.extraction.composition import (
    ChunkingTaskScheduler,
)


class PendingChunkingTaskScheduler(
    ChunkingTaskScheduler,
):

    async def ensure_ready_task(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        extracted_asset_id: UUID,
    ) -> None:
        raise NotImplementedError(
            "Chunking task scheduler is not wired yet"
        )

    async def dispatch_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        raise NotImplementedError(
            "Chunking dispatcher is not wired yet"
        )

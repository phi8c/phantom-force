from uuid import UUID

from integration.ingest.batch_finalizer import (
    IngestBatchFinalizer,
)
from module.ingest.embedding.composition import (
    BatchFinalizationSignal,
    BatchFinalizer,
)

from module.ingest.chunking.composition import (
    ChunkBatchCompletionService,
)


class ModuleBatchFinalizer(
    BatchFinalizer,
):

    def __init__(
        self,
        completion_service: ChunkBatchCompletionService,
    ):
        self._finalizer = IngestBatchFinalizer(
            completion_service=completion_service,
        )

    async def complete_embedding(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
    ) -> BatchFinalizationSignal:

        result = await self._finalizer.complete_embedding(
            ingestion_job_id=ingestion_job_id,
            batch_id=batch_id,
        )

        return BatchFinalizationSignal(
            dispatch_index=result.dispatch_index,
        )

    async def dispatch_index(
        self,
        ingestion_job_id: UUID,
    ) -> None:

        raise NotImplementedError(
            "Index dispatcher is not wired yet"
        )

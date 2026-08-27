from uuid import UUID

from module.ingest.chunking.domain.contracts.downstream_task_scheduler import (
    DownstreamSignals,
    DownstreamTaskScheduler,
)


class PendingDownstreamTaskScheduler(
    DownstreamTaskScheduler,
):

    async def schedule(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        batch_id: UUID,
    ) -> DownstreamSignals:
        raise NotImplementedError(
            "Downstream task scheduler is not wired yet"
        )

    async def dispatch_embedding(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        raise NotImplementedError(
            "Embedding dispatcher is not wired yet"
        )

    async def dispatch_classification(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        raise NotImplementedError(
            "Classification dispatcher is not wired yet"
        )

from uuid import UUID

from module.ingest.chunking.composition import (
    ChunkBatchCompletionService,
    DownstreamSignals,
    DownstreamTaskScheduler,
)
from module.ingest.classification.composition import (
    ClassificationDispatcher,
    ClassificationTaskSchedulingService,
)
from module.ingest.embedding.composition import (
    EmbeddingDispatcher,
    EmbeddingTaskSchedulingService,
)


class ModuleDownstreamTaskScheduler(
    DownstreamTaskScheduler,
):

    def __init__(
        self,
        *,
        batch_completion_service: ChunkBatchCompletionService,
        embedding_scheduling_service: EmbeddingTaskSchedulingService,
        classification_scheduling_service: (
            ClassificationTaskSchedulingService
        ),
        embedding_dispatcher: EmbeddingDispatcher,
        classification_dispatcher: ClassificationDispatcher,
    ):
        self.batch_completion_service = (
            batch_completion_service
        )
        self.embedding_scheduling_service = (
            embedding_scheduling_service
        )
        self.classification_scheduling_service = (
            classification_scheduling_service
        )
        self.embedding_dispatcher = embedding_dispatcher
        self.classification_dispatcher = (
            classification_dispatcher
        )

    async def schedule(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        batch_id: UUID,
    ) -> DownstreamSignals:

        embedding_result = (
            await self.embedding_scheduling_service.schedule(
                ingestion_job_id=ingestion_job_id,
                document_id=document_id,
                batch_id=batch_id,
            )
        )

        classification_result = (
            await self.classification_scheduling_service.schedule(
                ingestion_job_id=ingestion_job_id,
                document_id=document_id,
                batch_id=batch_id,
            )
        )

        if classification_result.mark_chunk_batch_completed:
            await (
                self.batch_completion_service
                .mark_classification_completed(
                    batch_id,
                )
            )

        return DownstreamSignals(
            dispatch_embedding=embedding_result.dispatch,
            dispatch_classification=(
                classification_result.dispatch
            ),
            classification_skipped=(
                classification_result.mark_chunk_batch_completed
                and not classification_result.dispatch
            ),
        )

    async def dispatch_embedding(
        self,
        ingestion_job_id: UUID,
    ) -> None:

        await self.embedding_dispatcher.dispatch_job(
            ingestion_job_id,
        )

    async def dispatch_classification(
        self,
        ingestion_job_id: UUID,
    ) -> None:

        await self.classification_dispatcher.dispatch_job(
            ingestion_job_id,
        )

from datetime import datetime
from datetime import timezone
from uuid import UUID

from module.ingest.chunking.domain.contracts.downstream_task_scheduler import (
    DownstreamSignals,
    DownstreamTaskScheduler,
)
from module.ingest.chunking.domain.contracts.chunk_batch_completion_service import (
    ChunkBatchCompletionService,
)
from module.ingest.chunking.domain.contracts.document_chunk_query import (
    DocumentChunkQuery,
)
from module.ingest.classification.domain.contracts.classification_dispatcher import (
    ClassificationDispatcher,
)
from module.ingest.classification.domain.entities.chunk_classification import (
    ChunkClassification,
)
from module.ingest.classification.domain.entities.classification_task import (
    ClassificationTask,
)
from module.ingest.classification.domain.enums.task_status import (
    TaskStatus as ClassificationTaskStatus,
)
from module.ingest.classification.domain.contracts.classification_task_repository import (
    ClassificationTaskRepository,
)
from module.ingest.classification.domain.contracts.chunk_classification_repository import (
    ChunkClassificationRepository,
)
from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.embedding.domain.contracts.embedding_dispatcher import (
    EmbeddingDispatcher,
)
from module.ingest.embedding.domain.entities.embedding_task import (
    EmbeddingTask,
)
from module.ingest.embedding.domain.enums.task_status import (
    TaskStatus as EmbeddingTaskStatus,
)
from module.ingest.embedding.domain.contracts.embedding_task_repository import (
    EmbeddingTaskRepository,
)


class ModuleDownstreamTaskScheduler(
    DownstreamTaskScheduler,
):

    def __init__(
        self,
        *,
        ingestion_config_repository: IngestionConfigRepository,
        chunk_query: DocumentChunkQuery,
        batch_completion_service: ChunkBatchCompletionService,
        embedding_task_repository: EmbeddingTaskRepository,
        classification_task_repository: ClassificationTaskRepository,
        chunk_classification_repository: ChunkClassificationRepository,
        embedding_dispatcher: EmbeddingDispatcher,
        classification_dispatcher: ClassificationDispatcher,
    ):
        self.ingestion_config_repository = (
            ingestion_config_repository
        )
        self.chunk_query = chunk_query
        self.batch_completion_service = (
            batch_completion_service
        )
        self.embedding_task_repository = (
            embedding_task_repository
        )
        self.classification_task_repository = (
            classification_task_repository
        )
        self.chunk_classification_repository = (
            chunk_classification_repository
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

        dispatch_embedding = await self._ensure_embedding_task(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
            batch_id=batch_id,
        )

        classification_enabled = (
            await self._classification_enabled(
                ingestion_job_id,
            )
        )

        (
            dispatch_classification,
            mark_classification_completed,
        ) = (
            await self._ensure_classification_task(
                ingestion_job_id=ingestion_job_id,
                document_id=document_id,
                batch_id=batch_id,
                enabled=classification_enabled,
            )
        )

        if mark_classification_completed:
            await self._ensure_default_classifications(
                batch_id,
            )
            await (
                self.batch_completion_service
                .mark_classification_completed(
                    batch_id,
                )
            )

        return DownstreamSignals(
            dispatch_embedding=dispatch_embedding,
            dispatch_classification=dispatch_classification,
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

    async def _ensure_embedding_task(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        batch_id: UUID,
    ) -> bool:

        existing = (
            await self.embedding_task_repository
            .get_by_batch_id(
                batch_id,
            )
        )

        if existing is not None:
            return existing.status in {
                EmbeddingTaskStatus.READY,
                EmbeddingTaskStatus.PROCESSING,
            }

        await self.embedding_task_repository.create(
            EmbeddingTask(
                id=None,
                ingestion_job_id=ingestion_job_id,
                batch_id=batch_id,
                document_id=document_id,
                status=EmbeddingTaskStatus.READY,
                attempt_count=0,
                claimed_by=None,
                lease_until=None,
                error=None,
                created_at=None,
                updated_at=None,
                completed_at=None,
            )
        )

        return True

    async def _ensure_classification_task(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        batch_id: UUID,
        enabled: bool,
    ) -> tuple[bool, bool]:

        existing = (
            await self.classification_task_repository
            .get_by_batch_id(
                batch_id,
            )
        )

        if existing is not None:
            if existing.status in {
                ClassificationTaskStatus.READY,
                ClassificationTaskStatus.PROCESSING,
            }:
                return True, False

            return (
                False,
                existing.status in {
                    ClassificationTaskStatus.COMPLETED,
                    ClassificationTaskStatus.SKIPPED,
                },
            )

        now = datetime.now(
            timezone.utc,
        )

        await self.classification_task_repository.create(
            ClassificationTask(
                id=None,
                ingestion_job_id=ingestion_job_id,
                batch_id=batch_id,
                document_id=document_id,
                status=(
                    ClassificationTaskStatus.READY
                    if enabled
                    else ClassificationTaskStatus.SKIPPED
                ),
                attempt_count=0,
                claimed_by=None,
                lease_until=None,
                error=None,
                created_at=None,
                updated_at=None,
                completed_at=(
                    None
                    if enabled
                    else now
                ),
            )
        )

        return enabled, not enabled

    async def _classification_enabled(
        self,
        ingestion_job_id: UUID,
    ) -> bool:

        configuration = await (
            self.ingestion_config_repository
            .get_configuration_by_job_id(
                ingestion_job_id,
            )
        )

        if configuration is None:
            return False

        return bool(
            configuration.is_classification
        )

    async def _ensure_default_classifications(
        self,
        batch_id: UUID,
    ) -> None:

        chunks = await self.chunk_query.list_by_batch_id(
            batch_id,
        )

        classifications = [
            ChunkClassification(
                id=None,
                chunk_id=chunk.id,
                model_name="classification_disabled",
                label="disabled",
                confidence=None,
                raw_response={
                    "classification": "disabled",
                },
                created_at=None,
            )
            for chunk in chunks
        ]

        await (
            self.chunk_classification_repository
            .upsert_many(
                classifications,
            )
        )

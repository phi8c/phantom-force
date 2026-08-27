from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.domain.contracts.downstream_task_scheduler import (
    DownstreamSignals,
    DownstreamTaskScheduler,
)
from module.ingest.chunking.infrastructure.persistence.models.chunk_batch_model import (
    ChunkBatchModel,
)
from module.ingest.chunking.infrastructure.persistence.models.document_chunk_model import (
    DocumentChunkModel,
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
from module.ingest.classification.infrastructure.persistence.repositories.classification_task_repository_impl import (
    ClassificationTaskRepositoryImpl,
)
from module.ingest.classification.infrastructure.persistence.repositories.chunk_classification_repository_impl import (
    ChunkClassificationRepositoryImpl,
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
from module.ingest.embedding.infrastructure.persistence.repositories.embedding_task_repository_impl import (
    EmbeddingTaskRepositoryImpl,
)


class ModuleDownstreamTaskScheduler(
    DownstreamTaskScheduler,
):

    def __init__(
        self,
        *,
        session: AsyncSession,
        ingestion_config_repository: IngestionConfigRepository,
        embedding_task_repository: EmbeddingTaskRepositoryImpl,
        classification_task_repository: ClassificationTaskRepositoryImpl,
        chunk_classification_repository: ChunkClassificationRepositoryImpl,
        embedding_dispatcher: EmbeddingDispatcher,
        classification_dispatcher: ClassificationDispatcher,
    ):
        self.session = session
        self.ingestion_config_repository = (
            ingestion_config_repository
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
            await self._mark_classification_completed(
                batch_id,
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

    async def _mark_classification_completed(
        self,
        batch_id: UUID,
    ) -> None:

        statement = select(
            ChunkBatchModel
        ).where(
            ChunkBatchModel.id == batch_id,
        ).with_for_update()

        result = await self.session.execute(
            statement,
        )

        batch = result.scalar_one_or_none()

        if batch is None:
            raise ValueError(
                "Document chunk batch not found"
            )

        if batch.classification_completed:
            return

        batch.classification_completed = True
        batch.updated_at = datetime.now(
            timezone.utc,
        )

        await self.session.flush()

    async def _ensure_default_classifications(
        self,
        batch_id: UUID,
    ) -> None:

        statement = select(
            DocumentChunkModel
        ).where(
            DocumentChunkModel.batch_id
            == batch_id,
        )

        result = await self.session.execute(
            statement,
        )

        classifications = [
            ChunkClassification(
                id=None,
                batch_id=batch_id,
                chunk_id=chunk.id,
                sensitivity=1,
                metadata={
                    "classification": "disabled",
                },
                created_at=None,
                updated_at=None,
            )
            for chunk in result.scalars().all()
        ]

        await (
            self.chunk_classification_repository
            .upsert_many(
                classifications,
            )
        )

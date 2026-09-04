from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from uuid import UUID

from module.ingest.chunking.composition import (
    DocumentChunkQuery,
)
from module.ingest.classification.domain.contracts.chunk_classification_repository import (
    ChunkClassificationRepository,
)
from module.ingest.classification.domain.contracts.classification_task_repository import (
    ClassificationTaskRepository,
)
from module.ingest.classification.domain.entities.chunk_classification import (
    ChunkClassification,
)
from module.ingest.classification.domain.entities.classification_task import (
    ClassificationTask,
)
from module.ingest.classification.domain.enums.task_status import (
    TaskStatus,
)
from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)


@dataclass(frozen=True)
class ClassificationTaskSchedulingResult:
    dispatch: bool
    mark_chunk_batch_completed: bool


class ClassificationTaskSchedulingService:

    def __init__(
        self,
        *,
        ingestion_config_repository: IngestionConfigRepository,
        task_repository: ClassificationTaskRepository,
        classification_repository: ChunkClassificationRepository,
        chunk_query: DocumentChunkQuery,
    ):
        self.ingestion_config_repository = (
            ingestion_config_repository
        )
        self.task_repository = task_repository
        self.classification_repository = classification_repository
        self.chunk_query = chunk_query

    async def schedule(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        batch_id: UUID,
    ) -> ClassificationTaskSchedulingResult:

        enabled = await self._classification_enabled(
            ingestion_job_id,
        )

        existing_task = await self.task_repository.get_by_batch_id(
            batch_id,
        )

        if existing_task is not None:
            if existing_task.status in {
                TaskStatus.READY,
                TaskStatus.PROCESSING,
            }:
                return ClassificationTaskSchedulingResult(
                    dispatch=True,
                    mark_chunk_batch_completed=False,
                )

            return ClassificationTaskSchedulingResult(
                dispatch=False,
                mark_chunk_batch_completed=existing_task.status
                in {
                    TaskStatus.COMPLETED,
                    TaskStatus.SKIPPED,
                },
            )

        now = datetime.now(
            timezone.utc,
        )

        await self.task_repository.create(
            ClassificationTask(
                id=None,
                ingestion_job_id=ingestion_job_id,
                batch_id=batch_id,
                document_id=document_id,
                status=(
                    TaskStatus.READY
                    if enabled
                    else TaskStatus.SKIPPED
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

        if not enabled:
            await self._ensure_default_classifications(
                batch_id,
            )

        return ClassificationTaskSchedulingResult(
            dispatch=enabled,
            mark_chunk_batch_completed=not enabled,
        )

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

        await self.classification_repository.upsert_many(
            classifications,
        )

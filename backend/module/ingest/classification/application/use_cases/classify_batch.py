from datetime import datetime
from datetime import timezone
from uuid import UUID

from module.ingest.classification.domain.contracts.batch_finalizer import (
    BatchFinalizer,
)
from module.ingest.classification.domain.contracts.chunk_classification_repository import (
    ChunkClassificationRepository,
)
from module.ingest.classification.domain.contracts.chunk_reader import (
    ChunkReader,
)
from module.ingest.classification.domain.contracts.classification_engine import (
    ClassificationEngine,
)
from module.ingest.classification.domain.contracts.classification_task_repository import (
    ClassificationTaskRepository,
)
from module.ingest.classification.domain.contracts.unit_of_work import (
    UnitOfWork,
)
from module.ingest.classification.domain.entities.chunk_classification import (
    ChunkClassification,
)
from module.ingest.classification.domain.enums.task_status import (
    TaskStatus,
)


class ClassifyBatchUseCase:

    def __init__(
        self,
        *,
        task_repository: ClassificationTaskRepository,
        chunk_reader: ChunkReader,
        classification_engine: ClassificationEngine,
        classification_repository: ChunkClassificationRepository,
        batch_finalizer: BatchFinalizer,
        uow: UnitOfWork,
        max_attempts: int = 3,
    ):
        self.task_repository = task_repository
        self.chunk_reader = chunk_reader
        self.classification_engine = classification_engine
        self.classification_repository = (
            classification_repository
        )
        self.batch_finalizer = batch_finalizer
        self.uow = uow
        self.max_attempts = max_attempts

    async def execute(
        self,
        task_id: UUID,
    ) -> None:

        task = await self.task_repository.get_by_id(
            task_id,
        )

        if task is None:
            raise ValueError(
                "Classification task not found"
            )

        if task.status == TaskStatus.SKIPPED:
            await self._complete_skipped(
                task_id,
            )
            return

        if task.status != TaskStatus.PROCESSING:
            raise ValueError(
                "Classification task must be PROCESSING"
            )

        try:
            chunks = await self.chunk_reader.list_by_batch_id(
                task.batch_id,
            )

            results = await (
                self.classification_engine
                .classify_batch(
                    chunks,
                )
            )

            classifications = [
                ChunkClassification(
                    id=None,
                    batch_id=task.batch_id,
                    chunk_id=result.chunk_id,
                    sensitivity=result.sensitivity,
                    metadata=result.metadata,
                    created_at=None,
                    updated_at=None,
                )
                for result in results
            ]

            await self.classification_repository.upsert_many(
                classifications,
            )

            signal = (
                await self.batch_finalizer
                .complete_classification(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    batch_id=task.batch_id,
                )
            )

            task.status = TaskStatus.COMPLETED
            task.claimed_by = None
            task.lease_until = None
            task.error = None
            task.completed_at = datetime.now(
                timezone.utc,
            )

            await self.task_repository.update(
                task,
            )

            await self.uow.commit()

            if signal.dispatch_index:
                await self.batch_finalizer.dispatch_index(
                    task.ingestion_job_id,
                )

        except Exception as exc:
            await self.uow.rollback()

            task = await self.task_repository.get_by_id(
                task_id,
            )

            if task is not None:
                if (
                    task.attempt_count
                    >= self.max_attempts
                ):
                    task.status = TaskStatus.FAILED
                else:
                    task.status = TaskStatus.READY

                task.claimed_by = None
                task.lease_until = None
                task.error = str(exc)

                await self.task_repository.update(
                    task,
                )

                await self.uow.commit()

            raise

    async def _complete_skipped(
        self,
        task_id: UUID,
    ) -> None:

        task = await self.task_repository.get_by_id(
            task_id,
        )

        if task is None:
            raise ValueError(
                "Classification task not found"
            )

        signal = (
            await self.batch_finalizer
            .complete_classification(
                ingestion_job_id=task.ingestion_job_id,
                batch_id=task.batch_id,
            )
        )

        await self.uow.commit()

        if signal.dispatch_index:
            await self.batch_finalizer.dispatch_index(
                task.ingestion_job_id,
            )

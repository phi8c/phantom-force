from dataclasses import dataclass
from uuid import UUID

from module.ingest.embedding.domain.contracts.embedding_task_repository import (
    EmbeddingTaskRepository,
)
from module.ingest.embedding.domain.entities.embedding_task import (
    EmbeddingTask,
)
from module.ingest.embedding.domain.enums.task_status import (
    TaskStatus,
)


@dataclass(frozen=True)
class EmbeddingTaskSchedulingResult:
    dispatch: bool


class EmbeddingTaskSchedulingService:

    def __init__(
        self,
        task_repository: EmbeddingTaskRepository,
    ):
        self.task_repository = task_repository

    async def schedule(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        batch_id: UUID,
    ) -> EmbeddingTaskSchedulingResult:

        existing_task = await self.task_repository.get_by_batch_id(
            batch_id,
        )

        if existing_task is not None:
            return EmbeddingTaskSchedulingResult(
                dispatch=existing_task.status
                in {
                    TaskStatus.READY,
                    TaskStatus.PROCESSING,
                },
            )

        await self.task_repository.create(
            EmbeddingTask(
                id=None,
                ingestion_job_id=ingestion_job_id,
                batch_id=batch_id,
                document_id=document_id,
                status=TaskStatus.READY,
                attempt_count=0,
                claimed_by=None,
                lease_until=None,
                error=None,
                created_at=None,
                updated_at=None,
                completed_at=None,
            )
        )

        return EmbeddingTaskSchedulingResult(
            dispatch=True,
        )

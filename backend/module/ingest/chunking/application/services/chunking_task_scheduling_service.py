from dataclasses import dataclass
from uuid import UUID

from module.ingest.chunking.domain.contracts.chunking_task_repository import (
    ChunkingTaskRepository,
)
from module.ingest.chunking.domain.entities.chunking_task import (
    ChunkingTask,
)
from module.ingest.chunking.domain.enums.task_status import (
    TaskStatus,
)


@dataclass(frozen=True)
class ChunkingTaskSchedulingResult:
    dispatch: bool


class ChunkingTaskSchedulingService:

    def __init__(
        self,
        task_repository: ChunkingTaskRepository,
    ):
        self.task_repository = task_repository

    async def schedule(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ChunkingTaskSchedulingResult:

        existing_task = (
            await self.task_repository
            .get_by_job_and_document(
                ingestion_job_id=ingestion_job_id,
                document_id=document_id,
            )
        )

        if existing_task is not None:
            return ChunkingTaskSchedulingResult(
                dispatch=False,
            )

        await self.task_repository.create(
            ChunkingTask(
                id=None,
                ingestion_job_id=ingestion_job_id,
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

        return ChunkingTaskSchedulingResult(
            dispatch=True,
        )

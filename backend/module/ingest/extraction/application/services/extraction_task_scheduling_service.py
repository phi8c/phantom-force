from dataclasses import dataclass
from uuid import UUID

from module.ingest.extraction.domain.contracts.extraction_task_repository import (
    ExtractionTaskRepository,
)
from module.ingest.extraction.domain.entities.extraction_task import (
    ExtractionTask,
)
from module.ingest.extraction.domain.enums.task_status import (
    TaskStatus,
)


@dataclass(frozen=True)
class ExtractionTaskSchedulingResult:
    dispatch: bool


class ExtractionTaskSchedulingService:

    def __init__(
        self,
        task_repository: ExtractionTaskRepository,
    ):
        self.task_repository = task_repository

    async def schedule(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ExtractionTaskSchedulingResult:

        existing_task = (
            await self.task_repository
            .get_by_job_and_document(
                ingestion_job_id=ingestion_job_id,
                document_id=document_id,
            )
        )

        if existing_task is not None:
            return ExtractionTaskSchedulingResult(
                dispatch=False,
            )

        await self.task_repository.create(
            ExtractionTask(
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

        return ExtractionTaskSchedulingResult(
            dispatch=True,
        )

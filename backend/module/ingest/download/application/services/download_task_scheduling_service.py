from dataclasses import dataclass
from uuid import UUID

from module.ingest.download.domain.contracts.download_task_repository import (
    DownloadTaskRepository,
)
from module.ingest.download.domain.entities.download_task import (
    DownloadTask,
)
from module.ingest.download.domain.enums.task_status import (
    TaskStatus,
)


@dataclass(frozen=True)
class DownloadTaskSchedulingResult:
    dispatch: bool


class DownloadTaskSchedulingService:

    def __init__(
        self,
        task_repository: DownloadTaskRepository,
    ):
        self.task_repository = task_repository

    async def schedule(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> DownloadTaskSchedulingResult:

        existing_task = (
            await self.task_repository
            .get_by_job_and_document(
                ingestion_job_id=ingestion_job_id,
                document_id=document_id,
            )
        )

        if existing_task is not None:
            return DownloadTaskSchedulingResult(
                dispatch=False,
            )

        await self.task_repository.create(
            DownloadTask(
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

        return DownloadTaskSchedulingResult(
            dispatch=True,
        )

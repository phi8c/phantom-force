from uuid import UUID

from module.ingest.discovery.domain.contracts.download_task_scheduler import (
    DownloadTaskScheduler,
)
from module.ingest.download.domain.contracts.download_dispatcher import (
    DownloadDispatcher,
)
from module.ingest.download.domain.contracts.download_task_repository import (
    DownloadTaskRepository,
)
from module.ingest.download.domain.entities.download_task import (
    DownloadTask,
)
from module.ingest.download.domain.enums.task_status import (
    TaskStatus,
)


class ModuleDownloadTaskScheduler(
    DownloadTaskScheduler,
):

    def __init__(
        self,
        task_repository: DownloadTaskRepository,
        dispatcher: DownloadDispatcher,
    ):
        self._task_repository = task_repository
        self._dispatcher = dispatcher

    async def ensure_ready_task(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> None:

        existing_task = (
            await self._task_repository
            .get_by_job_and_document(
                ingestion_job_id=ingestion_job_id,
                document_id=document_id,
            )
        )

        if existing_task is not None:
            return

        await self._task_repository.create(
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

    async def dispatch_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        await self._dispatcher.dispatch(
            ingestion_job_id,
        )

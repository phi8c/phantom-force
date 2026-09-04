from uuid import UUID

from module.ingest.discovery.composition import (
    DownloadTaskScheduler,
)
from module.ingest.download.composition import (
    DownloadDispatcher,
    DownloadTaskSchedulingService,
)


class ModuleDownloadTaskScheduler(
    DownloadTaskScheduler,
):

    def __init__(
        self,
        scheduling_service: DownloadTaskSchedulingService,
        dispatcher: DownloadDispatcher,
    ):
        self._scheduling_service = scheduling_service
        self._dispatcher = dispatcher

    async def ensure_ready_task(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> None:

        await self._scheduling_service.schedule(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
        )

    async def dispatch_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        await self._dispatcher.dispatch(
            ingestion_job_id,
        )

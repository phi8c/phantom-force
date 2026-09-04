from uuid import UUID

from module.ingest.download.composition import (
    ExtractionTaskScheduler,
)
from module.ingest.extraction.composition import (
    ExtractionDispatcher,
    ExtractionTaskSchedulingService,
)


class ModuleExtractionTaskScheduler(
    ExtractionTaskScheduler,
):

    def __init__(
        self,
        scheduling_service: ExtractionTaskSchedulingService,
        dispatcher: ExtractionDispatcher,
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

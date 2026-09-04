from uuid import UUID

from module.ingest.chunking.composition import (
    ChunkingDispatcher,
    ChunkingTaskSchedulingService,
)
from module.ingest.extraction.composition import (
    ChunkingTaskScheduler,
)


class ModuleChunkingTaskScheduler(
    ChunkingTaskScheduler,
):

    def __init__(
        self,
        scheduling_service: ChunkingTaskSchedulingService,
        dispatcher: ChunkingDispatcher,
    ):
        self._scheduling_service = scheduling_service
        self._dispatcher = dispatcher

    async def ensure_ready_task(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        extracted_asset_id: UUID,
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

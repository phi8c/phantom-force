from uuid import UUID

from module.ingest.chunking.domain.contracts.chunking_dispatcher import (
    ChunkingDispatcher,
)
from module.ingest.chunking.domain.contracts.chunking_task_repository import (
    ChunkingTaskRepository,
)
from module.ingest.chunking.domain.entities.chunking_task import (
    ChunkingTask,
)
from module.ingest.chunking.domain.enums.task_status import (
    TaskStatus,
)
from module.ingest.extraction.domain.contracts.chunking_task_scheduler import (
    ChunkingTaskScheduler,
)


class ModuleChunkingTaskScheduler(
    ChunkingTaskScheduler,
):

    def __init__(
        self,
        task_repository: ChunkingTaskRepository,
        dispatcher: ChunkingDispatcher,
    ):
        self._task_repository = task_repository
        self._dispatcher = dispatcher

    async def ensure_ready_task(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        extracted_asset_id: UUID,
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

    async def dispatch_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        await self._dispatcher.dispatch(
            ingestion_job_id,
        )

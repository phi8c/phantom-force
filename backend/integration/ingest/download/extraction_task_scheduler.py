from uuid import UUID

from module.ingest.download.domain.contracts.extraction_task_scheduler import (
    ExtractionTaskScheduler,
)
from module.ingest.extraction.domain.contracts.extraction_dispatcher import (
    ExtractionDispatcher,
)
from module.ingest.extraction.domain.contracts.extraction_task_repository import (
    ExtractionTaskRepository,
)
from module.ingest.extraction.domain.entities.extraction_task import (
    ExtractionTask,
)
from module.ingest.extraction.domain.enums.task_status import (
    TaskStatus,
)


class ModuleExtractionTaskScheduler(
    ExtractionTaskScheduler,
):

    def __init__(
        self,
        task_repository: ExtractionTaskRepository,
        dispatcher: ExtractionDispatcher,
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

    async def dispatch_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        await self._dispatcher.dispatch(
            ingestion_job_id,
        )

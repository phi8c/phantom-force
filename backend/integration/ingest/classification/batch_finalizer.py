from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from integration.ingest.batch_finalizer import (
    IngestBatchFinalizer,
)
from module.ingest.classification.domain.contracts.batch_finalizer import (
    BatchFinalizationSignal,
    BatchFinalizer,
)


class ModuleBatchFinalizer(
    BatchFinalizer,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self._finalizer = IngestBatchFinalizer(
            session=session,
        )

    async def complete_classification(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
    ) -> BatchFinalizationSignal:

        result = await (
            self._finalizer
            .complete_classification(
                ingestion_job_id=ingestion_job_id,
                batch_id=batch_id,
            )
        )

        return BatchFinalizationSignal(
            dispatch_index=result.dispatch_index,
        )

    async def dispatch_index(
        self,
        ingestion_job_id: UUID,
    ) -> None:

        raise NotImplementedError(
            "Index dispatcher is not wired yet"
        )

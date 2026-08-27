from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.infrastructure.persistence.models.chunk_batch_model import (
    ChunkBatchModel,
)


@dataclass(frozen=True)
class BatchCompletionResult:
    dispatch_index: bool


class IngestBatchFinalizer:

    def __init__(
        self,
        session: AsyncSession,
        dispatch_index_enabled: bool = False,
    ):
        self.session = session
        self.dispatch_index_enabled = (
            dispatch_index_enabled
        )

    async def complete_embedding(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
    ) -> BatchCompletionResult:

        return await self._complete(
            ingestion_job_id=ingestion_job_id,
            batch_id=batch_id,
            embedding_completed=True,
        )

    async def complete_classification(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
    ) -> BatchCompletionResult:

        return await self._complete(
            ingestion_job_id=ingestion_job_id,
            batch_id=batch_id,
            classification_completed=True,
        )

    async def _complete(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
        embedding_completed: bool = False,
        classification_completed: bool = False,
    ) -> BatchCompletionResult:

        statement = (
            select(
                ChunkBatchModel
            )
            .where(
                ChunkBatchModel.id == batch_id,
                ChunkBatchModel.ingestion_job_id
                == ingestion_job_id,
            )
            .with_for_update()
        )

        result = await self.session.execute(
            statement,
        )

        batch = result.scalar_one_or_none()

        if batch is None:
            raise ValueError(
                "Document chunk batch not found"
            )

        now = datetime.now(
            timezone.utc,
        )

        if embedding_completed:
            batch.embedding_completed = True

        if classification_completed:
            batch.classification_completed = True

        dispatch_index = False

        if (
            batch.embedding_completed
            and batch.classification_completed
            and not batch.batch_completed
        ):
            batch.batch_completed = True
            dispatch_index = True

        batch.updated_at = now

        await self.session.flush()

        return BatchCompletionResult(
            dispatch_index=(
                dispatch_index
                and self.dispatch_index_enabled
            ),
        )

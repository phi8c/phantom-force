from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.domain.contracts.chunking_task_repository import (
    ChunkingTaskRepository,
)
from module.ingest.chunking.domain.entities.chunking_task import (
    ChunkingTask,
)
from module.ingest.chunking.domain.enums.task_status import (
    TaskStatus,
)
from module.ingest.chunking.infrastructure.persistence.mappers.chunking_task_mapper import (
    ChunkingTaskMapper,
)
from module.ingest.chunking.infrastructure.persistence.models.chunking_task_model import (
    ChunkingTaskModel,
)


class ChunkingTaskRepositoryImpl(
    ChunkingTaskRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        task_id: UUID,
    ) -> ChunkingTask | None:

        model = await self.session.get(
            ChunkingTaskModel,
            task_id,
        )

        if model is None:
            return None

        return ChunkingTaskMapper.to_entity(
            model,
        )

    async def get_by_job_and_document(
        self,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ChunkingTask | None:

        statement = select(
            ChunkingTaskModel
        ).where(
            ChunkingTaskModel.ingestion_job_id
            == ingestion_job_id,
            ChunkingTaskModel.document_id
            == document_id,
        )

        result = await self.session.execute(
            statement,
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ChunkingTaskMapper.to_entity(
            model,
        )

    async def create(
        self,
        task: ChunkingTask,
    ) -> ChunkingTask:

        model = ChunkingTaskMapper.to_model(
            task,
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return ChunkingTaskMapper.to_entity(
            model,
        )

    async def update(
        self,
        task: ChunkingTask,
    ) -> ChunkingTask:

        if task.id is None:
            raise ValueError(
                "ChunkingTask id is required for update"
            )

        model = await self.session.get(
            ChunkingTaskModel,
            task.id,
        )

        if model is None:
            raise ValueError(
                "ChunkingTask not found"
            )

        model.status = task.status.value
        model.attempt_count = task.attempt_count
        model.claimed_by = task.claimed_by
        model.lease_until = task.lease_until
        model.error = task.error
        model.completed_at = task.completed_at
        model.updated_at = datetime.now(
            timezone.utc,
        )

        await self.session.flush()

        return ChunkingTaskMapper.to_entity(
            model,
        )

    async def claim_ready(
        self,
        ingestion_job_id: UUID,
        *,
        limit: int,
        claimed_by: str,
        lease_until: datetime,
    ) -> list[ChunkingTask]:

        now = datetime.now(
            timezone.utc,
        )

        statement = (
            select(
                ChunkingTaskModel
            )
            .where(
                ChunkingTaskModel.ingestion_job_id
                == ingestion_job_id,
                or_(
                    ChunkingTaskModel.status
                    == TaskStatus.READY.value,
                    (
                        (
                            ChunkingTaskModel.status
                            == TaskStatus.PROCESSING.value
                        )
                        & (
                            ChunkingTaskModel.lease_until
                            < now
                        )
                    ),
                ),
            )
            .order_by(
                ChunkingTaskModel.created_at.asc(),
            )
            .limit(
                limit,
            )
            .with_for_update(
                skip_locked=True,
            )
        )

        result = await self.session.execute(
            statement,
        )

        models = result.scalars().all()

        for model in models:
            model.status = TaskStatus.PROCESSING.value
            model.claimed_by = claimed_by
            model.lease_until = lease_until
            model.attempt_count = (
                model.attempt_count + 1
            )
            model.error = None
            model.updated_at = now

        await self.session.flush()

        return [
            ChunkingTaskMapper.to_entity(
                model
            )
            for model in models
        ]

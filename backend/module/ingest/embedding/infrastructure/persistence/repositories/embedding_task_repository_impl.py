from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.embedding.domain.contracts.embedding_task_repository import (
    EmbeddingTaskRepository,
)
from module.ingest.embedding.domain.entities.embedding_task import (
    EmbeddingTask,
)
from module.ingest.embedding.domain.enums.task_status import (
    TaskStatus,
)
from module.ingest.embedding.infrastructure.persistence.mappers.embedding_task_mapper import (
    EmbeddingTaskMapper,
)
from module.ingest.embedding.infrastructure.persistence.models.embedding_task_model import (
    EmbeddingTaskModel,
)


class EmbeddingTaskRepositoryImpl(
    EmbeddingTaskRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        task_id: UUID,
    ) -> EmbeddingTask | None:

        model = await self.session.get(
            EmbeddingTaskModel,
            task_id,
        )

        if model is None:
            return None

        return EmbeddingTaskMapper.to_entity(
            model,
        )

    async def get_by_batch_id(
        self,
        batch_id: UUID,
    ) -> EmbeddingTask | None:

        statement = select(
            EmbeddingTaskModel
        ).where(
            EmbeddingTaskModel.batch_id
            == batch_id,
        )

        result = await self.session.execute(
            statement,
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return EmbeddingTaskMapper.to_entity(
            model,
        )

    async def create(
        self,
        task: EmbeddingTask,
    ) -> EmbeddingTask:

        model = EmbeddingTaskMapper.to_model(
            task,
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return EmbeddingTaskMapper.to_entity(
            model,
        )

    async def update(
        self,
        task: EmbeddingTask,
    ) -> EmbeddingTask:

        if task.id is None:
            raise ValueError(
                "EmbeddingTask id is required for update"
            )

        model = await self.session.get(
            EmbeddingTaskModel,
            task.id,
        )

        if model is None:
            raise ValueError(
                "EmbeddingTask not found"
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

        return EmbeddingTaskMapper.to_entity(
            model,
        )

    async def claim_ready(
        self,
        ingestion_job_id: UUID,
        *,
        limit: int,
        claimed_by: str,
        lease_until: datetime,
    ) -> list[EmbeddingTask]:

        now = datetime.now(
            timezone.utc,
        )

        statement = (
            select(
                EmbeddingTaskModel
            )
            .where(
                EmbeddingTaskModel.ingestion_job_id
                == ingestion_job_id,
                or_(
                    EmbeddingTaskModel.status
                    == TaskStatus.READY.value,
                    (
                        (
                            EmbeddingTaskModel.status
                            == TaskStatus.PROCESSING.value
                        )
                        & (
                            EmbeddingTaskModel.lease_until
                            < now
                        )
                    ),
                ),
            )
            .order_by(
                EmbeddingTaskModel.created_at.asc(),
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
            EmbeddingTaskMapper.to_entity(
                model
            )
            for model in models
        ]

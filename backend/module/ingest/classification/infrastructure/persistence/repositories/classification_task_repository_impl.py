from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.classification.domain.contracts.classification_task_repository import (
    ClassificationTaskRepository,
)
from module.ingest.classification.domain.entities.classification_task import (
    ClassificationTask,
)
from module.ingest.classification.domain.enums.task_status import (
    TaskStatus,
)
from module.ingest.classification.infrastructure.persistence.mappers.classification_task_mapper import (
    ClassificationTaskMapper,
)
from module.ingest.classification.infrastructure.persistence.models.classification_task_model import (
    ClassificationTaskModel,
)


class ClassificationTaskRepositoryImpl(
    ClassificationTaskRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        task_id: UUID,
    ) -> ClassificationTask | None:

        model = await self.session.get(
            ClassificationTaskModel,
            task_id,
        )

        if model is None:
            return None

        return ClassificationTaskMapper.to_entity(
            model,
        )

    async def get_by_batch_id(
        self,
        batch_id: UUID,
    ) -> ClassificationTask | None:

        statement = select(
            ClassificationTaskModel
        ).where(
            ClassificationTaskModel.batch_id
            == batch_id,
        )

        result = await self.session.execute(
            statement,
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ClassificationTaskMapper.to_entity(
            model,
        )

    async def create(
        self,
        task: ClassificationTask,
    ) -> ClassificationTask:

        model = ClassificationTaskMapper.to_model(
            task,
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return ClassificationTaskMapper.to_entity(
            model,
        )

    async def update(
        self,
        task: ClassificationTask,
    ) -> ClassificationTask:

        if task.id is None:
            raise ValueError(
                "ClassificationTask id is required for update"
            )

        model = await self.session.get(
            ClassificationTaskModel,
            task.id,
        )

        if model is None:
            raise ValueError(
                "ClassificationTask not found"
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

        return ClassificationTaskMapper.to_entity(
            model,
        )

    async def claim_ready(
        self,
        ingestion_job_id: UUID,
        *,
        limit: int,
        claimed_by: str,
        lease_until: datetime,
    ) -> list[ClassificationTask]:

        now = datetime.now(
            timezone.utc,
        )

        statement = (
            select(
                ClassificationTaskModel
            )
            .where(
                ClassificationTaskModel.ingestion_job_id
                == ingestion_job_id,
                or_(
                    ClassificationTaskModel.status
                    == TaskStatus.READY.value,
                    (
                        (
                            ClassificationTaskModel.status
                            == TaskStatus.PROCESSING.value
                        )
                        & (
                            ClassificationTaskModel.lease_until
                            < now
                        )
                    ),
                ),
            )
            .order_by(
                ClassificationTaskModel.created_at.asc(),
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
            ClassificationTaskMapper.to_entity(
                model
            )
            for model in models
        ]

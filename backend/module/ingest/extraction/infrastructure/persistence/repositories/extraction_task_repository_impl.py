from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.extraction.domain.contracts.extraction_task_repository import (
    ExtractionTaskRepository,
)
from module.ingest.extraction.domain.entities.extraction_task import (
    ExtractionTask,
)
from module.ingest.extraction.domain.enums.task_status import (
    TaskStatus,
)
from module.ingest.extraction.infrastructure.persistence.mappers.extraction_task_mapper import (
    ExtractionTaskMapper,
)
from module.ingest.extraction.infrastructure.persistence.models.extraction_task_model import (
    ExtractionTaskModel,
)


class ExtractionTaskRepositoryImpl(
    ExtractionTaskRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        task_id: UUID,
    ) -> ExtractionTask | None:

        model = await self.session.get(
            ExtractionTaskModel,
            task_id,
        )

        if model is None:
            return None

        return ExtractionTaskMapper.to_entity(
            model,
        )

    async def get_by_job_and_document(
        self,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ExtractionTask | None:

        statement = select(
            ExtractionTaskModel
        ).where(
            ExtractionTaskModel.ingestion_job_id
            == ingestion_job_id,
            ExtractionTaskModel.document_id
            == document_id,
        )

        result = await self.session.execute(
            statement,
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ExtractionTaskMapper.to_entity(
            model,
        )

    async def create(
        self,
        task: ExtractionTask,
    ) -> ExtractionTask:

        model = ExtractionTaskMapper.to_model(
            task,
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return ExtractionTaskMapper.to_entity(
            model,
        )

    async def update(
        self,
        task: ExtractionTask,
    ) -> ExtractionTask:

        if task.id is None:
            raise ValueError(
                "ExtractionTask id is required for update"
            )

        model = await self.session.get(
            ExtractionTaskModel,
            task.id,
        )

        if model is None:
            raise ValueError(
                "ExtractionTask not found"
            )

        model.status = (
            task.status.value
        )

        model.attempt_count = (
            task.attempt_count
        )

        model.claimed_by = (
            task.claimed_by
        )

        model.lease_until = (
            task.lease_until
        )

        model.error = (
            task.error
        )

        model.completed_at = (
            task.completed_at
        )

        model.updated_at = datetime.now(
            timezone.utc,
        )

        await self.session.flush()

        return ExtractionTaskMapper.to_entity(
            model,
        )

    async def claim_ready(
        self,
        ingestion_job_id: UUID,
        *,
        limit: int,
        claimed_by: str,
        lease_until: datetime,
    ) -> list[ExtractionTask]:

        now = datetime.now(
            timezone.utc,
        )

        statement = (
            select(
                ExtractionTaskModel
            )
            .where(
                ExtractionTaskModel.ingestion_job_id
                == ingestion_job_id,
                or_(
                    ExtractionTaskModel.status
                    == TaskStatus.READY.value,
                    (
                        (
                            ExtractionTaskModel.status
                            == TaskStatus.PROCESSING.value
                        )
                        & (
                            ExtractionTaskModel.lease_until
                            < now
                        )
                    ),
                ),
            )
            .order_by(
                ExtractionTaskModel.created_at.asc(),
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
            model.status = (
                TaskStatus.PROCESSING.value
            )
            model.claimed_by = (
                claimed_by
            )
            model.lease_until = (
                lease_until
            )
            model.attempt_count = (
                model.attempt_count + 1
            )
            model.error = None
            model.updated_at = now

        await self.session.flush()

        return [
            ExtractionTaskMapper.to_entity(
                model
            )
            for model in models
        ]

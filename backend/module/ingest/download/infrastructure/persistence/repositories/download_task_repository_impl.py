from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.download.domain.contracts.download_task_repository import (
    DownloadTaskRepository,
)

from module.ingest.download.domain.entities.download_task import (
    DownloadTask,
)

from module.ingest.download.domain.enums.task_status import (
    TaskStatus,
)

from module.ingest.download.infrastructure.persistence.mappers.download_task_mapper import (
    DownloadTaskMapper,
)

from module.ingest.download.infrastructure.persistence.models.download_task_model import (
    DownloadTaskModel,
)


class DownloadTaskRepositoryImpl(
    DownloadTaskRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        task_id: UUID,
    ) -> DownloadTask | None:

        model = await self.session.get(
            DownloadTaskModel,
            task_id,
        )

        if model is None:
            return None

        return DownloadTaskMapper.to_entity(
            model,
        )

    async def get_by_job_and_document(
        self,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> DownloadTask | None:

        statement = select(
            DownloadTaskModel
        ).where(
            DownloadTaskModel.ingestion_job_id
            == ingestion_job_id,
            DownloadTaskModel.document_id
            == document_id,
        )

        result = await self.session.execute(
            statement,
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return DownloadTaskMapper.to_entity(
            model,
        )

    async def create(
        self,
        task: DownloadTask,
    ) -> DownloadTask:

        model = DownloadTaskMapper.to_model(
            task,
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return DownloadTaskMapper.to_entity(
            model,
        )

    async def update(
        self,
        task: DownloadTask,
    ) -> DownloadTask:

        if task.id is None:
            raise ValueError(
                "DownloadTask id is required for update"
            )

        model = await self.session.get(
            DownloadTaskModel,
            task.id,
        )

        if model is None:
            raise ValueError(
                "DownloadTask not found"
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

        return DownloadTaskMapper.to_entity(
            model,
        )

    async def claim_ready(
        self,
        ingestion_job_id: UUID,
        *,
        limit: int,
        claimed_by: str,
        lease_until: datetime,
    ) -> list[DownloadTask]:

        now = datetime.now(
            timezone.utc,
        )

        statement = (
            select(
                DownloadTaskModel
            )
            .where(
                DownloadTaskModel.ingestion_job_id
                == ingestion_job_id,
                or_(
                    DownloadTaskModel.status
                    == TaskStatus.READY.value,
                    (
                        (
                            DownloadTaskModel.status
                            == TaskStatus.PROCESSING.value
                        )
                        & (
                            DownloadTaskModel.lease_until
                            < now
                        )
                    ),
                ),
            )
            .order_by(
                DownloadTaskModel.created_at.asc(),
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
            DownloadTaskMapper.to_entity(
                model
            )
            for model in models
        ]
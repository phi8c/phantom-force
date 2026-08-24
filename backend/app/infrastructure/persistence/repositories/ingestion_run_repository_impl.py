from uuid import UUID

from app.domain.entities.ingestion_run import (
    IngestionRun,
)

from app.domain.repositories.ingestion_run_repository import (
    IngestionRunRepository,
)

from app.infrastructure.persistence.mappers.ingestion_run_mapper import (
    IngestionRunMapper,
)

from app.infrastructure.persistence.models.ingestion_run_model import (
    IngestionRunModel,
)

from app.shared.repositories.base_repository import (
    BaseRepository,
)


class IngestionRunRepositoryImpl(
    BaseRepository[IngestionRunModel],
    IngestionRunRepository,
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=IngestionRunModel,
        )

    async def get_by_id(
        self,
        job_id: UUID,
    ) -> IngestionRun | None:

        model = await super().get_by_id(
            job_id,
        )

        if not model:
            return None

        return IngestionRunMapper.to_entity(
            model,
        )

    async def create(
        self,
        job: IngestionRun,
    ) -> IngestionRun:

        model = IngestionRunMapper.to_model(
            job,
        )

        created_model = await self.add(
            model,
        )

        return IngestionRunMapper.to_entity(
            created_model,
        )

    async def update(
        self,
        job: IngestionRun,
    ) -> None:

        model = await super().get_by_id(
            job.id,
        )

        if not model:
            raise ValueError(
                "Job not found",
            )

        model.status = job.status

        model.total_files = (
            job.total_files
        )

        model.completed_files = (
            job.completed_files
        )

        model.failed_files = (
            job.failed_files
        )

        model.started_at = (
            job.started_at
        )

        model.finished_at = (
            job.finished_at
        )

        await self.session.flush()
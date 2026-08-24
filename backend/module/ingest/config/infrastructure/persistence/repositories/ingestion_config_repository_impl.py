from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)
from module.ingest.config.infrastructure.persistence.mappers.ingestion_job_configuration_mapper import (
    IngestionJobConfigurationMapper,
)
from module.ingest.config.infrastructure.persistence.mappers.ingestion_job_mapper import (
    IngestionJobMapper,
)
from module.ingest.config.infrastructure.persistence.models.ingestion_job_configuration_model import (
    IngestionJobConfigurationModel,
)
from module.ingest.config.infrastructure.persistence.models.ingestion_job_model import (
    IngestionJobModel,
)


class IngestionConfigRepositoryImpl(
    IngestionConfigRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_job_by_id(
        self,
        job_id: UUID,
    ) -> IngestionJob | None:

        result = await self.session.execute(
            select(
                IngestionJobModel,
            ).where(
                IngestionJobModel.id == job_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return IngestionJobMapper.to_entity(
            model,
        )

    async def get_configuration_by_job_id(
        self,
        job_id: UUID,
    ) -> IngestionJobConfiguration | None:

        result = await self.session.execute(
            select(
                IngestionJobConfigurationModel,
            ).where(
                IngestionJobConfigurationModel.ingestion_job_id
                == job_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return (
            IngestionJobConfigurationMapper.to_entity(
                model,
            )
        )

    async def get_job_with_configuration(
        self,
        job_id: UUID,
    ) -> tuple[
        IngestionJob,
        IngestionJobConfiguration,
    ] | None:

        result = await self.session.execute(
            select(
                IngestionJobModel,
                IngestionJobConfigurationModel,
            )
            .join(
                IngestionJobConfigurationModel,
                IngestionJobConfigurationModel.ingestion_job_id
                == IngestionJobModel.id,
            )
            .where(
                IngestionJobModel.id == job_id,
            )
        )

        row = result.one_or_none()

        if row is None:
            return None

        job_model, configuration_model = row

        return (
            IngestionJobMapper.to_entity(
                job_model,
            ),
            IngestionJobConfigurationMapper.to_entity(
                configuration_model,
            ),
        )
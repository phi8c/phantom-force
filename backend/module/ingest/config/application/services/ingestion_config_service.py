from uuid import UUID

from module.ingest.config.application.use_cases.get_ingestion_config import (
    GetIngestionConfigUseCase,
)
from module.ingest.config.application.use_cases.get_ingestion_job import (
    GetIngestionJobUseCase,
)
from module.ingest.config.application.use_cases.get_ingestion_job_configuration import (
    GetIngestionJobConfigurationUseCase,
)
from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)


class IngestionConfigService:

    def __init__(
        self,
        get_job: GetIngestionJobUseCase,
        get_configuration: GetIngestionJobConfigurationUseCase,
        get_config: GetIngestionConfigUseCase,
    ):
        self._get_job = get_job
        self._get_configuration = get_configuration
        self._get_config = get_config

    async def get_job(
        self,
        job_id: UUID,
    ) -> IngestionJob | None:

        return await self._get_job.execute(
            job_id,
        )

    async def get_configuration(
        self,
        job_id: UUID,
    ) -> IngestionJobConfiguration | None:

        return await self._get_configuration.execute(
            job_id,
        )

    async def get_config(
        self,
        job_id: UUID,
    ) -> tuple[
        IngestionJob,
        IngestionJobConfiguration,
    ] | None:

        return await self._get_config.execute(
            job_id,
        )
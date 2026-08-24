from uuid import UUID

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)


class GetIngestionJobConfigurationUseCase:

    def __init__(
        self,
        repository: IngestionConfigRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        job_id: UUID,
    ) -> IngestionJobConfiguration | None:

        return await (
            self.repository
            .get_configuration_by_job_id(
                job_id,
            )
        )
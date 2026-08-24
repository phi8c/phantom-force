from uuid import UUID

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)


class GetIngestionConfigUseCase:

    def __init__(
        self,
        repository: IngestionConfigRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        job_id: UUID,
    ) -> tuple[
        IngestionJob,
        IngestionJobConfiguration,
    ] | None:

        return await (
            self.repository
            .get_job_with_configuration(
                job_id,
            )
        )
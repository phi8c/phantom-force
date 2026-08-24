from uuid import UUID

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)


class GetIngestionJobUseCase:

    def __init__(
        self,
        repository: IngestionConfigRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        job_id: UUID,
    ) -> IngestionJob | None:

        return await self.repository.get_job_by_id(
            job_id,
        )
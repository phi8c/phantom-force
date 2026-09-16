from uuid import UUID

from module.ingest.config.application.dtos.ingestion_job_scope import (
    IngestionJobScopeEnvelope,
    IngestionJobScopeResponse,
)
from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)


class GetIngestionJobScopeUseCase:

    def __init__(
        self,
        repository: IngestionConfigRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        job_id: UUID,
    ) -> IngestionJobScopeEnvelope:

        job = await self.repository.get_job_by_id(
            job_id,
        )

        if job is None:
            raise LookupError(
                "ingestion_job_id was not found"
            )

        configured = (
            job.scope_type is not None
            and job.scope_data is not None
        )

        return IngestionJobScopeEnvelope(
            configured=configured,
            data=(
                IngestionJobScopeResponse(
                    ingestion_job_id=job_id,
                    scope_type=job.scope_type,
                    scope_data=job.scope_data,
                )
                if configured
                else None
            ),
        )

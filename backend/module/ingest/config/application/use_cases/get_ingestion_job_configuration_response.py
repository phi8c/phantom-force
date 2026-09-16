from uuid import UUID

from module.ingest.config.application.dtos.save_ingestion_job_configuration import (
    IngestionJobConfigurationEnvelope,
    IngestionJobConfigurationResponse,
)

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)


class GetIngestionJobConfigurationResponseUseCase:

    def __init__(
        self,
        repository: IngestionConfigRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        job_id: UUID,
    ) -> IngestionJobConfigurationEnvelope:

        job = await self.repository.get_job_by_id(
            job_id,
        )

        if job is None:
            raise LookupError(
                "ingestion_job_id was not found"
            )

        configuration = (
            await self.repository.get_configuration_by_job_id(
                job_id,
            )
        )

        return IngestionJobConfigurationEnvelope(
            configured=configuration is not None,
            data=(
                self._to_response(configuration)
                if configuration is not None
                else None
            ),
        )

    @staticmethod
    def _to_response(
        configuration: IngestionJobConfiguration,
    ) -> IngestionJobConfigurationResponse:
        if configuration.id is None:
            raise RuntimeError(
                "ingestion job configuration id was not generated"
            )

        return IngestionJobConfigurationResponse(
            id=configuration.id,
            ingestion_job_id=configuration.ingestion_job_id,
            is_classification=configuration.is_classification,
            model_set_id=configuration.model_set_id,
            chunking_strategy_id=(
                configuration.chunking_strategy_id
            ),
            extraction_engine_id=(
                configuration.extraction_engine_id
            ),
            configuration=configuration.configuration,
            created_at=configuration.created_at,
            updated_at=configuration.updated_at,
        )

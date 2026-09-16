from datetime import datetime
from datetime import timezone

from module.ingest.config.application.dtos.save_ingestion_job_configuration import (
    IngestionJobConfigurationResponse,
    SaveIngestionJobConfigurationCommand,
)
from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.config.domain.contracts.unit_of_work import (
    UnitOfWork,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)
from module.ingest.master.composition.master_config_resolver import (
    IngestionMasterConfigResolver,
)


class SaveIngestionJobConfigurationUseCase:

    def __init__(
        self,
        *,
        ingestion_config_repository: IngestionConfigRepository,
        master_config_resolver: IngestionMasterConfigResolver,
        uow: UnitOfWork,
    ):
        self.ingestion_config_repository = (
            ingestion_config_repository
        )
        self.master_config_resolver = master_config_resolver
        self.uow = uow

    async def execute(
        self,
        command: SaveIngestionJobConfigurationCommand,
    ) -> IngestionJobConfigurationResponse:

        job = await self.ingestion_config_repository.get_job_by_id(
            command.ingestion_job_id,
        )

        if job is None:
            raise LookupError(
                "ingestion_job_id was not found"
            )

        master_config = await self.master_config_resolver.resolve(
            extraction_engine_code=(
                command.extraction_engine_code
            ),
            chunking_strategy_code=(
                command.chunking_strategy_code
            ),
            model_set_code=command.model_set_code,
        )

        now = datetime.now(
            timezone.utc,
        )

        try:
            configuration = (
                await self.ingestion_config_repository
                .save_configuration(
                    IngestionJobConfiguration(
                        id=None,
                        ingestion_job_id=command.ingestion_job_id,
                        is_classification=(
                            command.is_classification
                        ),
                        model_set_id=master_config.model_set_id,
                        chunking_strategy_id=(
                            master_config.chunking_strategy_id
                        ),
                        extraction_engine_id=(
                            master_config.extraction_engine_id
                        ),
                        configuration=(
                            command.configuration or {}
                        ),
                        created_at=now,
                        updated_at=now,
                    )
                )
            )

            await self.uow.commit()

        except Exception:
            await self.uow.rollback()
            raise

        return self._to_response(
            configuration,
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

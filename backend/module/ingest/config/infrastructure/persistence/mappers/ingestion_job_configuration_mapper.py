from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)

from module.ingest.config.infrastructure.persistence.models.ingestion_job_configuration_model import (
    IngestionJobConfigurationModel,
)


class IngestionJobConfigurationMapper:

    @staticmethod
    def to_entity(
        model: IngestionJobConfigurationModel,
    ) -> IngestionJobConfiguration:

        return IngestionJobConfiguration(
            id=model.id,
            ingestion_job_id=model.ingestion_job_id,
            is_classification=model.is_classification,
            model_set_id=model.model_set_id,
            chunking_strategy_id=(
                model.chunking_strategy_id
            ),
            extraction_engine_id=(
                model.extraction_engine_id
            ),
            configuration=model.configuration,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: IngestionJobConfiguration,
    ) -> IngestionJobConfigurationModel:

        return IngestionJobConfigurationModel(
            id=entity.id,
            ingestion_job_id=entity.ingestion_job_id,
            is_classification=(
                entity.is_classification
            ),
            model_set_id=entity.model_set_id,
            chunking_strategy_id=(
                entity.chunking_strategy_id
            ),
            extraction_engine_id=(
                entity.extraction_engine_id
            ),
            configuration=entity.configuration,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


from app.domain.entities.ingestion_source import (
    IngestionSource,
)

from app.infrastructure.persistence.models.ingestion_source_model import (
    IngestionSourceModel,
)


class IngestionSourceMapper:

    @staticmethod
    def to_entity(
        model: IngestionSourceModel,
    ) -> IngestionSource:

        return IngestionSource(
    id=model.id,
    name=model.name,
    source_type=model.source_type,
    provider_type=model.provider_type,
    provider_configuration=model.provider_configuration,
    enabled=model.enabled,
)

    @staticmethod
    def to_model(
        entity: IngestionSource,
    ) -> IngestionSourceModel:

        return IngestionSourceModel(
            id=entity.id,
            name=entity.name,
            source_type=entity.source_type,
            provider_type=entity.provider_type,
            provider_configuration=entity.provider_configuration,
            enabled=entity.enabled,
        )
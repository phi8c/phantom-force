from module.ingest.master.extraction_strategy.domain.entities.extraction_strategy import (
    ExtractionStrategy,
)

from module.ingest.master.extraction_strategy.infrastructure.persistence.models.extraction_strategy_model import (
    ExtractionStrategyModel,
)


class ExtractionStrategyMapper:

    @staticmethod
    def to_entity(
        model: ExtractionStrategyModel,
    ) -> ExtractionStrategy:

        return ExtractionStrategy(
            id=model.id,
            code=model.code,
            name=model.name,
            provider=model.provider,
            configuration=model.configuration,
            enabled=model.enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: ExtractionStrategy,
    ) -> ExtractionStrategyModel:

        return ExtractionStrategyModel(
            id=entity.id,
            code=entity.code,
            name=entity.name,
            provider=entity.provider,
            configuration=entity.configuration,
            enabled=entity.enabled,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

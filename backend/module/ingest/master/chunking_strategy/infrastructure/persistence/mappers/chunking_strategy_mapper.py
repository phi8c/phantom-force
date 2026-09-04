from module.ingest.master.chunking_strategy.domain.entities.chunking_strategy import (
    ChunkingStrategy,
)

from module.ingest.master.chunking_strategy.infrastructure.persistence.models.chunking_strategy_model import (
    ChunkingStrategyModel,
)


class ChunkingStrategyMapper:

    @staticmethod
    def to_entity(
        model: ChunkingStrategyModel,
    ) -> ChunkingStrategy:

        return ChunkingStrategy(
            id=model.id,
            code=model.code,
            name=model.name,
            configuration=model.configuration,
            enabled=model.enabled,
            created_at=None,
            updated_at=None,
        )

    @staticmethod
    def to_model(
        entity: ChunkingStrategy,
    ) -> ChunkingStrategyModel:

        return ChunkingStrategyModel(
            id=entity.id,
            code=entity.code,
            name=entity.name,
            configuration=entity.configuration,
            enabled=entity.enabled,
        )

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
            created_at=model.created_at,
            updated_at=model.updated_at,
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
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
from app.application.chunking.chunking_engine import (
    ChunkingEngine,
)

from app.application.chunking.models.chunk_configuration import (
    ChunkConfiguration,
)

from app.application.chunking.resolvers.chunk_configuration_resolver import (
    ChunkConfigurationResolver,
)

from app.domain.enums.chunk_strategy_type import (
    ChunkStrategyType,
)


def get_chunking_engine():

    configuration = (
        ChunkConfiguration(
            strategy=(
                ChunkStrategyType.AUTO
            ),
            level=2,
            max_chunk_tokens=1500,
        )
    )

    resolver = (
        ChunkConfigurationResolver()
    )

    strategy = (
        resolver.resolve(
            configuration,
        )
    )

    return (
        ChunkingEngine(
            strategy=strategy,
        )
    )
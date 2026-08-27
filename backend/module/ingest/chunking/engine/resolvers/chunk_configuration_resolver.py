from module.ingest.chunking.engine.models.chunk_configuration import (
    ChunkConfiguration,
)

from module.ingest.chunking.engine.strategies.auto_chunk_strategy import (
    AutoChunkStrategy,
)

from module.ingest.chunking.engine.strategies.level_chunk_strategy import (
    LevelChunkStrategy,
)

from module.ingest.chunking.engine.enums.chunk_strategy_type import (
    ChunkStrategyType,
)


class ChunkConfigurationResolver:

    def resolve(
        self,
        configuration: ChunkConfiguration,
    ):

        if (
            configuration.strategy
            == ChunkStrategyType.LEVEL
        ):
            return (
                LevelChunkStrategy(
                    level=(
                        configuration.level
                        or 2
                    ),
                )
            )

        return (
            AutoChunkStrategy(
                level=(
                    configuration.level
                    or 2
                ),
                max_chunk_tokens=(
                    configuration.max_chunk_tokens
                ),
            )
        )

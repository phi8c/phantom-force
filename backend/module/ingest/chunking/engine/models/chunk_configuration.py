from dataclasses import dataclass

from module.ingest.chunking.engine.enums.chunk_strategy_type import (
    ChunkStrategyType,
)


@dataclass(
    slots=True,
    frozen=True,
)
class ChunkConfiguration:

    strategy: ChunkStrategyType

    level: int | None

    max_chunk_tokens: int

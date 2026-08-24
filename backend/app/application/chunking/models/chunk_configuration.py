from dataclasses import dataclass

from app.domain.enums.chunk_strategy_type import ChunkStrategyType


@dataclass(
    slots=True,
    frozen=True,
)
class ChunkConfiguration:

    strategy: ChunkStrategyType

    level: int | None

    max_chunk_tokens: int
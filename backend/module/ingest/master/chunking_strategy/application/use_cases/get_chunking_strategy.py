from uuid import UUID

from module.ingest.master.chunking_strategy.domain.contracts.chunking_strategy_repository import (
    ChunkingStrategyRepository,
)
from module.ingest.master.chunking_strategy.domain.entities.chunking_strategy import (
    ChunkingStrategy,
)


class GetChunkingStrategyUseCase:

    def __init__(
        self,
        repository: ChunkingStrategyRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        strategy_id: UUID,
    ) -> ChunkingStrategy | None:

        return await self.repository.get_by_id(
            strategy_id,
        )
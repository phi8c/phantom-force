from module.ingest.master.chunking_strategy.domain.contracts.chunking_strategy_repository import (
    ChunkingStrategyRepository,
)
from module.ingest.master.chunking_strategy.domain.entities.chunking_strategy import (
    ChunkingStrategy,
)


class ListChunkingStrategiesUseCase:

    def __init__(
        self,
        repository: ChunkingStrategyRepository,
    ):
        self.repository = repository

    async def execute(
        self,
    ) -> list[ChunkingStrategy]:

        return await self.repository.list_enabled()

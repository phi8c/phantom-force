from uuid import UUID

from module.ingest.master.chunking_strategy.application.use_cases.get_chunking_strategy import (
    GetChunkingStrategyUseCase,
)
from module.ingest.master.chunking_strategy.application.use_cases.get_chunking_strategy_by_code import (
    GetChunkingStrategyByCodeUseCase,
)
from module.ingest.master.chunking_strategy.domain.entities.chunking_strategy import (
    ChunkingStrategy,
)


class ChunkingStrategyService:

    def __init__(
        self,
        get_strategy: GetChunkingStrategyUseCase,
        get_strategy_by_code: GetChunkingStrategyByCodeUseCase,
    ):
        self._get_strategy = get_strategy
        self._get_strategy_by_code = (
            get_strategy_by_code
        )

    async def get_by_id(
        self,
        strategy_id: UUID,
    ) -> ChunkingStrategy | None:

        return await self._get_strategy.execute(
            strategy_id,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> ChunkingStrategy | None:

        return await self._get_strategy_by_code.execute(
            code,
        )
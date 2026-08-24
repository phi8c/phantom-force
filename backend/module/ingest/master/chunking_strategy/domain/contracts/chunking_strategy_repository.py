from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.master.chunking_strategy.domain.entities.chunking_strategy import (
    ChunkingStrategy,
)


class ChunkingStrategyRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        strategy_id: UUID,
    ) -> ChunkingStrategy | None:
        pass

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> ChunkingStrategy | None:
        pass
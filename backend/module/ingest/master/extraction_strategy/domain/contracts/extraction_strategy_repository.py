from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.master.extraction_strategy.domain.entities.extraction_strategy import (
    ExtractionStrategy,
)


class ExtractionStrategyRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        strategy_id: UUID,
    ) -> ExtractionStrategy | None:
        pass

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> ExtractionStrategy | None:
        pass
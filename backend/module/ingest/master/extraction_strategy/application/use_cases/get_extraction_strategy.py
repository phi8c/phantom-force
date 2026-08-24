from uuid import UUID

from module.ingest.master.extraction_strategy.domain.contracts.extraction_strategy_repository import (
    ExtractionStrategyRepository,
)
from module.ingest.master.extraction_strategy.domain.entities.extraction_strategy import (
    ExtractionStrategy,
)


class GetExtractionStrategyUseCase:

    def __init__(
        self,
        repository: ExtractionStrategyRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        strategy_id: UUID,
    ) -> ExtractionStrategy | None:

        return await self.repository.get_by_id(
            strategy_id,
        )
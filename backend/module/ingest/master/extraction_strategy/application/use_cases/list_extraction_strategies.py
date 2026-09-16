from module.ingest.master.extraction_strategy.domain.contracts.extraction_strategy_repository import (
    ExtractionStrategyRepository,
)
from module.ingest.master.extraction_strategy.domain.entities.extraction_strategy import (
    ExtractionStrategy,
)


class ListExtractionStrategiesUseCase:

    def __init__(
        self,
        repository: ExtractionStrategyRepository,
    ):
        self.repository = repository

    async def execute(
        self,
    ) -> list[ExtractionStrategy]:

        return await self.repository.list_enabled()

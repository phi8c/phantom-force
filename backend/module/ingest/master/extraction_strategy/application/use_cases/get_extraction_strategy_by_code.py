from module.ingest.master.extraction_strategy.domain.contracts.extraction_strategy_repository import (
    ExtractionStrategyRepository,
)
from module.ingest.master.extraction_strategy.domain.entities.extraction_strategy import (
    ExtractionStrategy,
)


class GetExtractionStrategyByCodeUseCase:

    def __init__(
        self,
        repository: ExtractionStrategyRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        code: str,
    ) -> ExtractionStrategy | None:

        return await self.repository.get_by_code(
            code,
        )
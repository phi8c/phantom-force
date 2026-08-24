from uuid import UUID

from module.ingest.master.extraction_strategy.application.use_cases.get_extraction_strategy import (
    GetExtractionStrategyUseCase,
)
from module.ingest.master.extraction_strategy.application.use_cases.get_extraction_strategy_by_code import (
    GetExtractionStrategyByCodeUseCase,
)
from module.ingest.master.extraction_strategy.domain.entities.extraction_strategy import (
    ExtractionStrategy,
)


class ExtractionStrategyService:

    def __init__(
        self,
        get_strategy: GetExtractionStrategyUseCase,
        get_strategy_by_code: GetExtractionStrategyByCodeUseCase,
    ):
        self._get_strategy = get_strategy
        self._get_strategy_by_code = (
            get_strategy_by_code
        )

    async def get_by_id(
        self,
        strategy_id: UUID,
    ) -> ExtractionStrategy | None:

        return await self._get_strategy.execute(
            strategy_id,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> ExtractionStrategy | None:

        return await (
            self._get_strategy_by_code.execute(
                code,
            )
        )
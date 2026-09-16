from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.master.extraction_strategy.application.services.extraction_strategy_service import (
    ExtractionStrategyService,
)
from module.ingest.master.extraction_strategy.application.use_cases.get_extraction_strategy import (
    GetExtractionStrategyUseCase,
)
from module.ingest.master.extraction_strategy.application.use_cases.get_extraction_strategy_by_code import (
    GetExtractionStrategyByCodeUseCase,
)
from module.ingest.master.extraction_strategy.application.use_cases.list_extraction_strategies import (
    ListExtractionStrategiesUseCase,
)
from module.ingest.master.extraction_strategy.infrastructure.persistence.repositories.extraction_strategy_repository_impl import (
    ExtractionStrategyRepositoryImpl,
)


def create_extraction_strategy_service(
    session: AsyncSession,
) -> ExtractionStrategyService:

    repository = ExtractionStrategyRepositoryImpl(
        session=session,
    )

    get_strategy = GetExtractionStrategyUseCase(
        repository=repository,
    )

    get_strategy_by_code = (
        GetExtractionStrategyByCodeUseCase(
            repository=repository,
        )
    )
    list_strategies = ListExtractionStrategiesUseCase(
        repository=repository,
    )

    return ExtractionStrategyService(
        get_strategy=get_strategy,
        get_strategy_by_code=get_strategy_by_code,
        list_strategies=list_strategies,
    )

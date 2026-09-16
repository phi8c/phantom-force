from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.master.chunking_strategy.application.services.chunking_strategy_service import (
    ChunkingStrategyService,
)
from module.ingest.master.chunking_strategy.application.use_cases.get_chunking_strategy import (
    GetChunkingStrategyUseCase,
)
from module.ingest.master.chunking_strategy.application.use_cases.get_chunking_strategy_by_code import (
    GetChunkingStrategyByCodeUseCase,
)
from module.ingest.master.chunking_strategy.application.use_cases.list_chunking_strategies import (
    ListChunkingStrategiesUseCase,
)
from module.ingest.master.chunking_strategy.infrastructure.persistence.repositories.chunking_strategy_repository_impl import (
    ChunkingStrategyRepositoryImpl,
)


def create_chunking_strategy_service(
    session: AsyncSession,
) -> ChunkingStrategyService:

    repository = ChunkingStrategyRepositoryImpl(
        session=session,
    )

    get_strategy = GetChunkingStrategyUseCase(
        repository=repository,
    )

    get_strategy_by_code = (
        GetChunkingStrategyByCodeUseCase(
            repository=repository,
        )
    )
    list_strategies = ListChunkingStrategiesUseCase(
        repository=repository,
    )

    return ChunkingStrategyService(
        get_strategy=get_strategy,
        get_strategy_by_code=get_strategy_by_code,
        list_strategies=list_strategies,
    )

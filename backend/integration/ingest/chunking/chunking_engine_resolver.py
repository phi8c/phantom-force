from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from integration.ingest.chunking.chunking_engine import (
    LegacyChunkingEngineAdapter,
)
from module.ingest.chunking.domain.contracts.chunking_engine import (
    ChunkingEngine,
)
from module.ingest.chunking.domain.contracts.chunking_engine_resolver import (
    ChunkingEngineResolver,
)
from module.ingest.chunking.engine.strategies.auto_chunk_strategy import (
    AutoChunkStrategy,
)
from module.ingest.chunking.engine.strategies.level_chunk_strategy import (
    LevelChunkStrategy,
)
from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import (
    IngestionConfigRepositoryImpl,
)
from module.ingest.master.chunking_strategy.infrastructure.persistence.repositories.chunking_strategy_repository_impl import (
    ChunkingStrategyRepositoryImpl,
)


class DbChunkingEngineResolver(
    ChunkingEngineResolver,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self._configuration_repository = (
            IngestionConfigRepositoryImpl(
                session=session,
            )
        )
        self._chunking_repository = (
            ChunkingStrategyRepositoryImpl(
                session=session,
            )
        )

    async def resolve_for_job(
        self,
        ingestion_job_id: UUID,
    ) -> ChunkingEngine:

        configuration = (
            await self._configuration_repository
            .get_configuration_by_job_id(
                ingestion_job_id,
            )
        )

        if configuration is None:
            raise ValueError(
                "Ingestion job configuration not found"
            )

        chunking_strategy = (
            await self._chunking_repository
            .get_by_id(
                configuration.chunking_strategy_id,
            )
        )

        if (
            chunking_strategy is None
            or not chunking_strategy.enabled
        ):
            raise ValueError(
                "Chunking strategy is not available "
                "or disabled"
            )

        merged_configuration = {
            **(
                chunking_strategy.configuration
                or {}
            ),
            **(
                configuration.configuration
                or {}
            ),
        }

        return self._create_engine(
            code=chunking_strategy.code,
            configuration=merged_configuration,
        )

    def _create_engine(
        self,
        *,
        code: str,
        configuration: dict,
    ) -> ChunkingEngine:

        normalized_code = code.strip().upper()
        level = int(
            configuration.get(
                "level",
                2,
            )
        )
        max_chunk_tokens = int(
            configuration.get(
                "max_chunk_tokens",
                800,
            )
        )

        if normalized_code == "SECTION":
            return LegacyChunkingEngineAdapter(
                strategy=LevelChunkStrategy(
                    level=level,
                )
            )

        if normalized_code == "PARAGRAPH":
            return LegacyChunkingEngineAdapter(
                strategy=AutoChunkStrategy(
                    level=level,
                    max_chunk_tokens=max_chunk_tokens,
                )
            )

        raise ValueError(
            "Unsupported chunking strategy: "
            f"{code}"
        )

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.infrastructure.engine.chunking_engine import (
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


logger = logging.getLogger(__name__)


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

        strategy_config = (
            chunking_strategy.configuration
            or {}
        )
        job_config = (
            configuration.configuration
            or {}
        )

        logger.info(
            "chunking config_loaded job_id=%s strategy_code=%s "
            "strategy_config=%s job_config=%s",
            ingestion_job_id,
            chunking_strategy.code,
            strategy_config,
            job_config,
        )

        merged_configuration = {
            **strategy_config,
            **job_config,
        }

        logger.info(
            "chunking config_resolved job_id=%s strategy_code=%s "
            "strategy_config=%s job_config=%s merged_config=%s",
            ingestion_job_id,
            chunking_strategy.code,
            strategy_config,
            job_config,
            merged_configuration,
        )
        print(
            "chunking config_resolved "
            f"job_id={ingestion_job_id} "
            f"strategy_code={chunking_strategy.code} "
            f"strategy_config={strategy_config} "
            f"job_config={job_config} "
            f"merged_config={merged_configuration}",
            flush=True,
        )

        engine = self._create_engine(
            code=chunking_strategy.code,
            configuration=merged_configuration,
        )
        resolved_level = int(
            merged_configuration.get(
                "level",
                2,
            )
        )
        resolved_max_chunk_tokens = int(
            merged_configuration.get(
                "max_chunk_tokens",
                800,
            )
        )

        logger.info(
            "chunking engine_resolved job_id=%s strategy_code=%s "
            "level=%s max_chunk_tokens=%s engine=%s",
            ingestion_job_id,
            chunking_strategy.code,
            resolved_level,
            resolved_max_chunk_tokens,
            engine.__class__.__name__,
        )
        print(
            "chunking engine_resolved "
            f"job_id={ingestion_job_id} "
            f"strategy_code={chunking_strategy.code} "
            f"level={resolved_level} "
            f"max_chunk_tokens={resolved_max_chunk_tokens} "
            f"engine={engine.__class__.__name__}",
            flush=True,
        )

        return engine

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

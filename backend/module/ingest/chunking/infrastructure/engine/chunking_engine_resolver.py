import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.infrastructure.engine.streaming_chunking_engine import StreamingChunkingEngine
from module.ingest.chunking.domain.contracts.chunking_engine import (
    ChunkingEngine,
)
from module.ingest.chunking.domain.contracts.chunking_engine_resolver import (
    ChunkingEngineResolver,
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
        reviewer_factory=None,
    ):
        self._reviewer_factory = reviewer_factory
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
                4000 if chunking_strategy.code.strip().upper() == "SMART" else 800,
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

        if normalized_code == "SMART":
            runtime = configuration.get("chunking_runtime", {})
            counter_name = runtime.get("token_counter", "tiktoken")
            if counter_name == "tiktoken":
                from module.ingest.chunking.infrastructure.engine.token_counter import TiktokenCounter
                counter = TiktokenCounter(runtime.get("encoding_name", "cl100k_base"))
            elif counter_name == "utf8_upper_bound":
                from module.ingest.chunking.application.services.chunk_budget import Utf8UpperBoundCounter
                counter = Utf8UpperBoundCounter()  # bytes, not tokens: only for budgets expressed in bytes
            else:
                raise ValueError("Unsupported chunk token counter")
            from .smart_chunking_engine import SmartChunkingEngine
            return SmartChunkingEngine(
                target_tokens=int(configuration.get("target_tokens", 2000)),
                max_chunk_tokens=int(configuration.get("max_chunk_tokens", 4000)),
                reserve_tokens=int(runtime.get("context_reserve_tokens", 64)),
                include_heading_context=bool(configuration.get("include_heading_context", True)),
                counter=counter,
            )

        if normalized_code in {"SECTION", "PARAGRAPH"}:
            runtime = configuration.get("chunking_runtime", {})
            counter_name = runtime.get("token_counter", "utf8_upper_bound")
            counter = None
            if counter_name == "tiktoken":
                from module.ingest.chunking.infrastructure.engine.token_counter import TiktokenCounter
                counter = TiktokenCounter(runtime.get("encoding_name", "o200k_base"))
            elif counter_name != "utf8_upper_bound":
                raise ValueError("Unsupported chunk token counter")
            engine_class = StreamingChunkingEngine
            review_args = {}
            review = runtime.get("structure_review", {})
            if review.get("enabled", False):
                if self._reviewer_factory is None:
                    raise ValueError("Structure reviewer factory is not configured")
                from module.ingest.chunking.application.services.structure_review import StructureReviewPlanner
                from .reviewed_chunking_engine import ReviewedChunkingEngine
                engine_class = ReviewedChunkingEngine
                review_args['review_planner'] = StructureReviewPlanner(
                    self._reviewer_factory(review),
                    max_window_bytes=int(review.get('max_window_bytes', 32000)),
                    max_blocks=int(review.get('max_blocks', 40)),
                    timeout_seconds=float(review.get('timeout_seconds', 600)),
                    review_structured=review.get('review_structured', False),
                )
            return engine_class(
                strategy=normalized_code, level=level, max_chunk_tokens=max_chunk_tokens,
                reserve_tokens=int(runtime.get("context_reserve_tokens", 64)), counter=counter,
                **review_args,
            )

        raise ValueError(
            "Unsupported chunking strategy: "
            f"{code}"
        )

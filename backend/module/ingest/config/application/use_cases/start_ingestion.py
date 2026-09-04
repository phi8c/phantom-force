from datetime import datetime
from datetime import timezone
from uuid import UUID

from module.ingest.config.application.dtos.start_ingestion import (
    StartIngestionCommand,
    StartIngestionResult,
)
from module.ingest.config.domain.contracts.discovery_dispatcher import (
    DiscoveryDispatcher,
)
from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.config.domain.contracts.unit_of_work import (
    UnitOfWork,
)
from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)
from module.ingest.master.chunking_strategy.domain.contracts.chunking_strategy_repository import (
    ChunkingStrategyRepository,
)
from module.ingest.master.extraction_strategy.domain.contracts.extraction_strategy_repository import (
    ExtractionStrategyRepository,
)
from module.ingest.master.model_set.domain.contracts.model_set_repository import (
    ModelSetRepository,
)
from module.knowledge_space.domain.contracts.knowledge_space_repository import (
    KnowledgeSpaceRepository,
)


class StartIngestionUseCase:

    def __init__(
        self,
        *,
        knowledge_space_repository: KnowledgeSpaceRepository,
        ingestion_config_repository: IngestionConfigRepository,
        extraction_strategy_repository: ExtractionStrategyRepository,
        chunking_strategy_repository: ChunkingStrategyRepository,
        model_set_repository: ModelSetRepository,
        discovery_dispatcher: DiscoveryDispatcher,
        uow: UnitOfWork,
    ):
        self.knowledge_space_repository = (
            knowledge_space_repository
        )
        self.ingestion_config_repository = (
            ingestion_config_repository
        )
        self.extraction_strategy_repository = (
            extraction_strategy_repository
        )
        self.chunking_strategy_repository = (
            chunking_strategy_repository
        )
        self.model_set_repository = model_set_repository
        self.discovery_dispatcher = discovery_dispatcher
        self.uow = uow

    async def execute(
        self,
        command: StartIngestionCommand,
    ) -> StartIngestionResult:

        try:
            job_id = await self._create_job(
                command,
            )
            await self.uow.commit()

        except Exception:
            await self.uow.rollback()
            raise

        await self.discovery_dispatcher.dispatch(
            ingestion_job_id=job_id,
            batch_size=command.batch_size,
        )

        return StartIngestionResult(
            ingestion_job_id=job_id,
            status="QUEUED",
        )

    async def _create_job(
        self,
        command: StartIngestionCommand,
    ) -> UUID:

        self._validate_batch_size(
            command.batch_size,
        )

        knowledge_space = (
            await self.knowledge_space_repository.get_by_id(
                command.knowledge_space_id,
            )
        )

        if knowledge_space is None:
            raise LookupError(
                "knowledge_space_id was not found"
            )

        extraction_engine = (
            await self.extraction_strategy_repository
            .get_by_code(
                self._normalize_code(
                    command.extraction_engine_code,
                )
            )
        )

        if (
            extraction_engine is None
            or extraction_engine.id is None
            or not extraction_engine.enabled
        ):
            raise ValueError(
                "extraction_engine_code is not "
                "available or disabled"
            )

        chunking_strategy = (
            await self.chunking_strategy_repository
            .get_by_code(
                self._normalize_code(
                    command.chunking_strategy_code,
                )
            )
        )

        if (
            chunking_strategy is None
            or chunking_strategy.id is None
            or not chunking_strategy.enabled
        ):
            raise ValueError(
                "chunking_strategy_code is not "
                "available or disabled"
            )

        model_set_id = await self._resolve_model_set_id(
            command.model_set_code,
        )

        now = datetime.now(
            timezone.utc,
        )

        job = await self.ingestion_config_repository.add_job(
            IngestionJob(
                id=None,
                knowledge_space_id=command.knowledge_space_id,
                trigger_type=command.trigger_type,
                status="READY",
                is_build_graph=command.is_build_graph,
                total_files=0,
                completed_files=0,
                failed_files=0,
                started_at=None,
                finished_at=None,
                created_at=now,
                scope_type=command.scope_type,
                scope_data=command.scope_data or {},
            )
        )

        if job.id is None:
            raise RuntimeError(
                "ingestion job id was not generated"
            )

        await (
            self.ingestion_config_repository
            .add_configuration(
                IngestionJobConfiguration(
                    id=None,
                    ingestion_job_id=job.id,
                    is_classification=(
                        command.is_classification
                    ),
                    model_set_id=model_set_id,
                    chunking_strategy_id=(
                        chunking_strategy.id
                    ),
                    extraction_engine_id=(
                        extraction_engine.id
                    ),
                    configuration=(
                        command.configuration or {}
                    ),
                    created_at=now,
                    updated_at=now,
                )
            )
        )

        return job.id

    async def _resolve_model_set_id(
        self,
        code: str | None,
    ) -> UUID | None:

        if not code:
            return None

        model_set = await self.model_set_repository.get_by_code(
            self._normalize_code(
                code,
            )
        )

        if (
            model_set is None
            or model_set.id is None
            or not model_set.enabled
        ):
            raise ValueError(
                "model_set_code is not available "
                "or disabled"
            )

        return model_set.id

    @staticmethod
    def _validate_batch_size(
        batch_size: int,
    ) -> None:

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0"
            )

    @staticmethod
    def _normalize_code(
        code: str,
    ) -> str:

        normalized = code.strip().upper()

        if not normalized:
            raise ValueError(
                "code must not be empty"
            )

        return normalized

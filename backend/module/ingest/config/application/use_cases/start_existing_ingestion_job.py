from __future__ import annotations

from uuid import UUID

from module.ingest.config.application.dtos.start_existing_ingestion_job import (
    StartExistingIngestionJobCommand,
)
from module.ingest.config.application.dtos.start_existing_ingestion_job import (
    StartExistingIngestionJobResult,
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
from module.knowledge_space.domain.contracts.knowledge_space_data_hub_repository import (
    KnowledgeSpaceDataHubRepository,
)
from module.master_data.data_hub_providers.domain.contracts.data_hub_provider_repository import (
    DataHubProviderRepository,
)


class StartExistingIngestionJobUseCase:
    def __init__(
        self,
        *,
        ingestion_config_repository: IngestionConfigRepository,
        knowledge_space_data_hub_repository: (
            KnowledgeSpaceDataHubRepository
        ),
        data_hub_provider_repository: DataHubProviderRepository,
        discovery_dispatcher: DiscoveryDispatcher,
        uow: UnitOfWork,
    ) -> None:
        self._ingestion_config_repository = (
            ingestion_config_repository
        )
        self._knowledge_space_data_hub_repository = (
            knowledge_space_data_hub_repository
        )
        self._data_hub_provider_repository = (
            data_hub_provider_repository
        )
        self._discovery_dispatcher = discovery_dispatcher
        self._uow = uow

    async def execute(
        self,
        command: StartExistingIngestionJobCommand,
    ) -> StartExistingIngestionJobResult:
        self._validate_batch_size(
            command.batch_size,
        )

        try:
            await self._validate_ready_to_start(
                command.ingestion_job_id,
            )
            job = await (
                self._ingestion_config_repository.mark_job_ready(
                    job_id=command.ingestion_job_id,
                )
            )

            await self._uow.commit()

        except Exception:
            await self._uow.rollback()
            raise

        if job.id is None:
            raise RuntimeError(
                "ingestion job id was not generated"
            )

        await self._discovery_dispatcher.dispatch(
            ingestion_job_id=job.id,
            batch_size=command.batch_size,
        )

        return StartExistingIngestionJobResult(
            ingestion_job_id=job.id,
            status="QUEUED",
        )

    async def _validate_ready_to_start(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        job = await self._ingestion_config_repository.get_job_by_id(
            ingestion_job_id,
        )

        if job is None or job.id is None:
            raise LookupError(
                "ingestion_job_id was not found"
            )

        configuration = await (
            self._ingestion_config_repository
            .get_configuration_by_job_id(
                ingestion_job_id,
            )
        )

        if configuration is None:
            raise ValueError(
                "ingestion job configuration is required before start"
            )

        self._validate_scope(
            scope_type=job.scope_type,
            scope_data=job.scope_data,
        )

        data_hub = await (
            self._knowledge_space_data_hub_repository
            .get_by_knowledge_space_id(
                job.knowledge_space_id,
            )
        )

        if (
            data_hub is None
            or data_hub.id is None
            or not data_hub.enabled
        ):
            raise ValueError(
                "Knowledge Space Data Hub is not configured or enabled"
            )

        provider = await self._data_hub_provider_repository.get_by_id(
            data_hub.data_hub_provider_id,
        )

        if provider is None or not provider.enabled:
            raise ValueError(
                "Data Hub provider is not available or disabled"
            )

    @staticmethod
    def _validate_scope(
        *,
        scope_type: str | None,
        scope_data: dict | None,
    ) -> None:
        if not scope_type:
            raise ValueError(
                "ingestion job scope is required before start"
            )

        if scope_type != "SELECTED_ROOTS":
            raise ValueError(
                "unsupported ingestion job scope_type"
            )

        if not isinstance(scope_data, dict):
            raise ValueError(
                "ingestion job scope_data is required before start"
            )

        roots = scope_data.get("roots")
        if not isinstance(roots, list) or not roots:
            raise ValueError(
                "ingestion job scope_data.roots is required before start"
            )

        for root in roots:
            if not isinstance(root, dict):
                raise ValueError(
                    "ingestion job scope roots must be objects"
                )

            if not str(root.get("site_id") or "").strip():
                raise ValueError(
                    "ingestion job scope root site_id is required"
                )

            if not str(root.get("drive_id") or "").strip():
                raise ValueError(
                    "ingestion job scope root drive_id is required"
                )

    @staticmethod
    def _validate_batch_size(
        batch_size: int,
    ) -> None:
        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0"
            )

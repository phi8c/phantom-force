from uuid import UUID

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.discovery.domain.contracts.data_hub_source_catalog import (
    DataHubSourceCatalog,
    IngestionSourceConfig,
)
from module.knowledge_space.application.services.data_hub_configuration_resolver import (
    DataHubConfigurationDisabledError,
    DataHubConfigurationNotFoundError,
    KnowledgeSpaceDataHubConfigurationResolver,
)


class ModuleDataHubSourceCatalog(
    DataHubSourceCatalog,
):

    def __init__(
        self,
        ingestion_config_repository: IngestionConfigRepository,
        data_hub_configuration_resolver: KnowledgeSpaceDataHubConfigurationResolver,
    ):
        self._ingestion_config_repository = (
            ingestion_config_repository
        )
        self._data_hub_configuration_resolver = data_hub_configuration_resolver

    async def get_for_ingestion_job(
        self,
        ingestion_job_id: UUID,
    ) -> IngestionSourceConfig | None:

        job = (
            await self._ingestion_config_repository
            .get_job_by_id(
                ingestion_job_id,
            )
        )

        if job is None:
            return None

        try:
            resolved = await self._data_hub_configuration_resolver.resolve(
                job.knowledge_space_id
            )
        except (
            DataHubConfigurationDisabledError,
            DataHubConfigurationNotFoundError,
        ):
            return None

        return IngestionSourceConfig(
            data_hub_id=resolved.data_hub_id,
            provider=resolved.provider,
            configuration=dict(resolved.configuration),
            scope_data=dict(
                job.scope_data
                or {}
            ),
        )

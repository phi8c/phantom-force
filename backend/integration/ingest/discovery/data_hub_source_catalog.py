from uuid import UUID

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.discovery.domain.contracts.data_hub_source_catalog import (
    DataHubSourceCatalog,
    IngestionSourceConfig,
)
from module.knowledge_space.domain.contracts.knowledge_space_data_hub_repository import (
    KnowledgeSpaceDataHubRepository,
)
from module.master_data.data_hub_providers.domain.contracts.data_hub_provider_repository import (
    DataHubProviderRepository,
)


class ModuleDataHubSourceCatalog(
    DataHubSourceCatalog,
):

    def __init__(
        self,
        ingestion_config_repository: IngestionConfigRepository,
        knowledge_space_data_hub_repository: KnowledgeSpaceDataHubRepository,
        data_hub_provider_repository: DataHubProviderRepository,
    ):
        self._ingestion_config_repository = (
            ingestion_config_repository
        )
        self._knowledge_space_data_hub_repository = (
            knowledge_space_data_hub_repository
        )
        self._data_hub_provider_repository = (
            data_hub_provider_repository
        )

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

        data_hub = (
            await self._knowledge_space_data_hub_repository
            .get_by_knowledge_space_id(
                job.knowledge_space_id,
            )
        )

        if (
            data_hub is None
            or not data_hub.enabled
            or data_hub.id is None
        ):
            return None

        provider_config = (
            await self._data_hub_provider_repository
            .get_by_id(
                data_hub.data_hub_provider_id,
            )
        )

        if (
            provider_config is None
            or not provider_config.enabled
        ):
            return None

        return IngestionSourceConfig(
            data_hub_id=data_hub.id,
            provider=provider_config.provider,
            configuration=dict(
                data_hub.configuration
                or {}
            ),
            scope_data=dict(
                job.scope_data
                or {}
            ),
        )

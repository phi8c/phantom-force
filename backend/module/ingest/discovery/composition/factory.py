from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from module.data_platform.data_hub.sharepoint.composition import (
    DataHubProviderResolver,
)
from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import (
    IngestionConfigRepositoryImpl,
)
from module.ingest.discovery.application.use_cases.discover_batch import (
    DiscoverBatchUseCase,
)
from module.ingest.discovery.infrastructure.persistence.repositories.document_repository_impl import (
    DocumentRepositoryImpl,
)
from module.ingest.discovery.infrastructure.persistence.repositories.ingestion_discovery_state_repository_impl import (
    IngestionDiscoveryStateRepositoryImpl,
)
from module.ingest.discovery.infrastructure.persistence.repositories.ingestion_document_state_repository_impl import (
    IngestionDocumentStateRepositoryImpl,
)
from module.ingest.discovery.domain.contracts.download_task_scheduler import (
    DownloadTaskScheduler,
)
from module.ingest.discovery.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from module.ingest.orchestration.composition import (
    create_orchestration_progress_service,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_data_hub_repository_impl import (
    KnowledgeSpaceDataHubRepositoryImpl,
)
from module.knowledge_space.application.services.data_hub_configuration_resolver import (
    KnowledgeSpaceDataHubConfigurationResolver,
)
from module.master_data.data_hub_providers.infrastructure.persistence.repositories.data_hub_provider_repository_impl import (
    DataHubProviderRepositoryImpl,
)

from module.ingest.discovery.infrastructure.providers.data_hub_discovery_provider_resolver import (
    DataHubDiscoveryProviderResolver,
)
from module.ingest.discovery.infrastructure.catalog.data_hub_source_catalog import (
    ModuleDataHubSourceCatalog,
)


def create_discover_batch_use_case(
    *,
    session,
    data_hub_provider_resolver: DataHubProviderResolver,
    download_task_scheduler: DownloadTaskScheduler,
) -> DiscoverBatchUseCase:

    ingestion_config_repository = (
        IngestionConfigRepositoryImpl(
            session=session,
        )
    )

    knowledge_space_data_hub_repository = (
        KnowledgeSpaceDataHubRepositoryImpl(
            session=session,
        )
    )

    data_hub_provider_repository = (
        DataHubProviderRepositoryImpl(
            session=session,
        )
    )

    document_repository = DocumentRepositoryImpl(
        session=session,
    )

    ingestion_document_state_repository = (
        IngestionDocumentStateRepositoryImpl(
            session=session,
        )
    )

    discovery_state_repository = (
        IngestionDiscoveryStateRepositoryImpl(
            session=session,
        )
    )

    uow = SQLAlchemyUnitOfWork(
        session=session,
    )

    return DiscoverBatchUseCase(
        source_catalog=ModuleDataHubSourceCatalog(
            ingestion_config_repository=(
                ingestion_config_repository
            ),
            data_hub_configuration_resolver=(
                KnowledgeSpaceDataHubConfigurationResolver(
                    knowledge_space_data_hub_repository,
                    data_hub_provider_repository,
                )
            ),
        ),
        document_repository=document_repository,
        ingestion_document_state_repository=(
            ingestion_document_state_repository
        ),
        discovery_state_repository=(
            discovery_state_repository
        ),
        provider_resolver=DataHubDiscoveryProviderResolver(
            data_hub_provider_resolver=(
                data_hub_provider_resolver
            ),
        ),
        download_task_scheduler=download_task_scheduler,
        orchestration_progress_service=(
            create_orchestration_progress_service(
                session=session,
            )
        ),
        uow=uow,
    )


@asynccontextmanager
async def create_discover_batch_use_case_scope(
    *,
    session_factory,
    data_hub_provider_resolver: DataHubProviderResolver,
    download_task_scheduler: DownloadTaskScheduler,
) -> AsyncIterator[DiscoverBatchUseCase]:

    async with session_factory() as session:
        yield create_discover_batch_use_case(
            session=session,
            data_hub_provider_resolver=(
                data_hub_provider_resolver
            ),
            download_task_scheduler=download_task_scheduler,
        )

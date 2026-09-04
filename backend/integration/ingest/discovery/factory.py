from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from module.data_platform.data_hub.composition.provider_resolver import (
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
from module.ingest.download.domain.contracts.download_dispatcher import (
    DownloadDispatcher,
)
from module.ingest.download.infrastructure.persistence.repositories.download_task_repository_impl import (
    DownloadTaskRepositoryImpl,
)
from module.ingest.discovery.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_data_hub_repository_impl import (
    KnowledgeSpaceDataHubRepositoryImpl,
)
from module.master_data.data_hub_providers.infrastructure.persistence.repositories.data_hub_provider_repository_impl import (
    DataHubProviderRepositoryImpl,
)

from integration.ingest.discovery.data_hub_discovery_provider_resolver import (
    DataHubDiscoveryProviderResolver,
)
from integration.ingest.discovery.data_hub_source_catalog import (
    ModuleDataHubSourceCatalog,
)
from integration.ingest.discovery.download_task_scheduler import (
    ModuleDownloadTaskScheduler,
)


def create_discover_batch_use_case(
    *,
    session: AsyncSession,
    data_hub_provider_resolver: DataHubProviderResolver,
    download_dispatcher: DownloadDispatcher,
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

    download_task_repository = DownloadTaskRepositoryImpl(
        session=session,
    )

    uow = SQLAlchemyUnitOfWork(
        session=session,
    )

    return DiscoverBatchUseCase(
        source_catalog=ModuleDataHubSourceCatalog(
            ingestion_config_repository=(
                ingestion_config_repository
            ),
            knowledge_space_data_hub_repository=(
                knowledge_space_data_hub_repository
            ),
            data_hub_provider_repository=(
                data_hub_provider_repository
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
        download_task_scheduler=ModuleDownloadTaskScheduler(
            task_repository=download_task_repository,
            dispatcher=download_dispatcher,
        ),
        uow=uow,
    )


@asynccontextmanager
async def create_discover_batch_use_case_scope(
    *,
    session_factory,
    data_hub_provider_resolver: DataHubProviderResolver,
    download_dispatcher: DownloadDispatcher,
) -> AsyncIterator[DiscoverBatchUseCase]:

    async with session_factory() as session:
        yield create_discover_batch_use_case(
            session=session,
            data_hub_provider_resolver=(
                data_hub_provider_resolver
            ),
            download_dispatcher=download_dispatcher,
        )

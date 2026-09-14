from uuid import UUID

from module.ingest.discovery.application.dtos.requests.discover_batch_request import (
    DiscoverBatchRequest,
)
from module.ingest.discovery.application.dtos.responses.discover_batch_response import (
    DiscoverBatchResponse,
    DiscoveryItem,
)
from module.ingest.discovery.domain.contracts.data_hub_source_catalog import (
    DataHubSourceCatalog,
)
from module.ingest.discovery.domain.contracts.discovery_provider import (
    SourceReference,
)
from module.ingest.discovery.domain.contracts.discovery_provider_resolver import (
    DiscoveryProviderResolver,
)
from module.ingest.discovery.domain.contracts.document_repository import (
    DocumentRepository,
)
from module.ingest.discovery.domain.contracts.download_task_scheduler import (
    DownloadTaskScheduler,
)
from module.ingest.discovery.domain.contracts.ingestion_discovery_state_repository import (
    IngestionDiscoveryStateRepository,
)
from module.ingest.discovery.domain.contracts.ingestion_document_state_repository import (
    IngestionDocumentStateRepository,
)
from module.ingest.orchestration.application.services import (
    OrchestrationProgressService,
)
from module.ingest.discovery.domain.contracts.unit_of_work import (
    UnitOfWork,
)
from module.ingest.discovery.domain.entities.document import (
    Document,
)
from module.ingest.discovery.domain.entities.ingestion_document_state import (
    IngestionDocumentState,
)
from module.ingest.discovery.domain.enums.ingestion_document_status import (
    IngestionDocumentStatus,
)


class DiscoverBatchUseCase:

    def __init__(
        self,
        source_catalog: DataHubSourceCatalog,
        document_repository: DocumentRepository,
        ingestion_document_state_repository: IngestionDocumentStateRepository,
        discovery_state_repository: IngestionDiscoveryStateRepository,
        provider_resolver: DiscoveryProviderResolver,
        download_task_scheduler: DownloadTaskScheduler,
        orchestration_progress_service: (
            OrchestrationProgressService
        ),
        uow: UnitOfWork,
    ):
        self.source_catalog = source_catalog
        self.document_repository = document_repository
        self.ingestion_document_state_repository = (
            ingestion_document_state_repository
        )
        self.discovery_state_repository = (
            discovery_state_repository
        )
        self.provider_resolver = provider_resolver
        self.download_task_scheduler = (
            download_task_scheduler
        )
        self.orchestration_progress_service = (
            orchestration_progress_service
        )
        self.uow = uow

    async def execute(
        self,
        request: DiscoverBatchRequest,
    ) -> DiscoverBatchResponse:

        if request.batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0"
            )

        source_config = (
            await self.source_catalog
            .get_for_ingestion_job(
                request.ingestion_job_id,
            )
        )

        if source_config is None:
            raise ValueError(
                "Data Hub source is not available "
                "for this ingestion job"
            )

        discovery_state = (
            await self.discovery_state_repository
            .get_by_ingestion_job_id(
                request.ingestion_job_id,
            )
        )

        if (
            discovery_state is not None
            and discovery_state.completed
        ):
            return DiscoverBatchResponse(
                ingestion_job_id=(
                    request.ingestion_job_id
                ),
                items=[],
                has_more=False,
            )

        cursor = (
            discovery_state.cursor
            if discovery_state is not None
            else None
        )

        source_metadata = dict(
            source_config.configuration
            or {}
        )

        if source_config.scope_data:
            source_metadata.update(
                source_config.scope_data
            )

        source = SourceReference(
            provider=source_config.provider,
            identifier=str(
                source_config.data_hub_id
            ),
            metadata=source_metadata,
        )

        provider = (
            self.provider_resolver.resolve(
                provider=source_config.provider,
                configuration=(
                    source_config.configuration
                ),
            )
        )

        page = await provider.discover(
            source=source,
            cursor=cursor,
            limit=request.batch_size,
        )

        discovered_files = page.items

        if not discovered_files:
            await (
                self.discovery_state_repository
                .save_progress(
                    ingestion_job_id=(
                        request.ingestion_job_id
                    ),
                    cursor=page.next_cursor,
                    discovered_count=0,
                    completed=not page.has_more,
                )
            )

            await self.uow.commit()

            return DiscoverBatchResponse(
                ingestion_job_id=(
                    request.ingestion_job_id
                ),
                items=[],
                has_more=page.has_more,
            )

        external_file_ids = [
            item.external_file_id
            for item in discovered_files
        ]

        existing_documents = (
            await self.document_repository
            .get_by_external_file_ids(
                data_hub_id=(
                    source_config.data_hub_id
                ),
                external_file_ids=(
                    external_file_ids
                ),
            )
        )

        result_items: list[
            DiscoveryItem
        ] = []
        document_ids: list[UUID] = []

        for discovered_file in discovered_files:
            document = existing_documents.get(
                discovered_file.external_file_id
            )

            if document is None:
                document = Document(
                    id=None,
                    data_hub_id=(
                        source_config.data_hub_id
                    ),
                    external_file_id=(
                        discovered_file.external_file_id
                    ),
                    file_name=(
                        discovered_file.file_name
                    ),
                    provider_metadata=dict(
                        discovered_file.provider_metadata
                        or {}
                    ),
                    source_file_url=(
                        discovered_file.source_file_url
                    ),
                    file_extension=(
                        discovered_file.file_extension
                    ),
                    file_size_bytes=(
                        discovered_file.file_size_bytes
                    ),
                    original_file_path=(
                        discovered_file.original_file_path
                    ),
                    last_modified_at=(
                        discovered_file.last_modified_at
                    ),
                    department=None,
                    owner_role=None,
                    security_level=None,
                    document_type=None,
                    created_at=None,
                    updated_at=None,
                )

                document = (
                    await self.document_repository
                    .create(
                        document,
                    )
                )

            else:
                document.file_name = (
                    discovered_file.file_name
                )
                document.provider_metadata = dict(
                    discovered_file.provider_metadata
                    or {}
                )
                document.source_file_url = (
                    discovered_file.source_file_url
                )
                document.file_extension = (
                    discovered_file.file_extension
                )
                document.file_size_bytes = (
                    discovered_file.file_size_bytes
                )
                document.original_file_path = (
                    discovered_file.original_file_path
                )
                document.last_modified_at = (
                    discovered_file.last_modified_at
                )

                await self.document_repository.update(
                    document,
                )

            if document.id is None:
                raise ValueError(
                    "Document id was not generated"
                )

            state = (
                await self.ingestion_document_state_repository
                .get_by_document_and_ingestion_job(
                    document_id=document.id,
                    ingestion_job_id=(
                        request.ingestion_job_id
                    ),
                )
            )

            if state is None:
                state = IngestionDocumentState(
                    document_id=document.id,
                    ingestion_job_id=(
                        request.ingestion_job_id
                    ),
                    status=(
                        IngestionDocumentStatus.PENDING
                    ),
                    created_at=None,
                    updated_at=None,
                )

                await (
                    self.ingestion_document_state_repository
                    .create(
                        state,
                    )
                )

            await (
                self.download_task_scheduler
                .ensure_ready_task(
                    ingestion_job_id=(
                        request.ingestion_job_id
                    ),
                    document_id=document.id,
                )
            )

            document_ids.append(
                document.id,
            )

            result_items.append(
                DiscoveryItem(
                    document_id=document.id,
                    external_file_id=(
                        document.external_file_id
                    ),
                    file_name=(
                        document.file_name
                    ),
                )
            )

        await (
            self.orchestration_progress_service
            .create_discovery_batch(
                ingestion_job_id=(
                    request.ingestion_job_id
                ),
                document_ids=document_ids,
            )
        )

        await (
            self.discovery_state_repository
            .save_progress(
                ingestion_job_id=(
                    request.ingestion_job_id
                ),
                cursor=page.next_cursor,
                discovered_count=len(
                    discovered_files
                ),
                completed=not page.has_more,
            )
        )

        await self.uow.commit()

        await self.download_task_scheduler.dispatch_job(
            request.ingestion_job_id,
        )

        return DiscoverBatchResponse(
            ingestion_job_id=(
                request.ingestion_job_id
            ),
            items=result_items,
            has_more=page.has_more,
        )

from module.data_platform.data_hub.domain.value_objects.source_reference import (
    SourceReference,
)

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)

from module.ingest.discovery.application.dtos.requests.discover_batch_request import (
    DiscoverBatchRequest,
)

from module.ingest.discovery.application.dtos.responses.discover_batch_response import (
    DiscoverBatchResponse,
    DiscoveryItem,
)

from module.ingest.discovery.domain.contracts.document_repository import (
    DocumentRepository,
)

from module.ingest.discovery.domain.contracts.ingestion_discovery_state_repository import (
    IngestionDiscoveryStateRepository,
)

from module.ingest.discovery.domain.contracts.ingestion_document_state_repository import (
    IngestionDocumentStateRepository,
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

from module.knowledge_space.domain.contracts.knowledge_space_data_hub_repository import (
    KnowledgeSpaceDataHubRepository,
)

from module.master_data.data_hub_providers.domain.contracts.data_hub_provider_repository import (
    DataHubProviderRepository,
)


class DiscoverBatchUseCase:

    def __init__(
        self,
        ingestion_config_repository: IngestionConfigRepository,
        knowledge_space_data_hub_repository: KnowledgeSpaceDataHubRepository,
        data_hub_provider_repository: DataHubProviderRepository,
        document_repository: DocumentRepository,
        ingestion_document_state_repository: IngestionDocumentStateRepository,
        discovery_state_repository: IngestionDiscoveryStateRepository,
        provider_resolver,
        download_dispatcher,
        uow,
    ):
        self.ingestion_config_repository = (
            ingestion_config_repository
        )

        self.knowledge_space_data_hub_repository = (
            knowledge_space_data_hub_repository
        )

        self.data_hub_provider_repository = (
            data_hub_provider_repository
        )

        self.document_repository = (
            document_repository
        )

        self.ingestion_document_state_repository = (
            ingestion_document_state_repository
        )

        self.discovery_state_repository = (
            discovery_state_repository
        )

        self.provider_resolver = (
            provider_resolver
        )

        self.download_dispatcher = (
            download_dispatcher
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

        # =================================================
        # 1. Load ingestion job
        # =================================================

        job = (
            await self.ingestion_config_repository
            .get_job_by_id(
                request.ingestion_job_id,
            )
        )

        if job is None:
            raise ValueError(
                "Ingestion job not found"
            )

        # =================================================
        # 2. Resolve Knowledge Space Data Hub
        # =================================================

        data_hub = (
            await self.knowledge_space_data_hub_repository
            .get_by_knowledge_space_id(
                job.knowledge_space_id,
            )
        )

        if data_hub is None:
            raise ValueError(
                "Data Hub is not configured "
                "for this knowledge space"
            )

        if not data_hub.enabled:
            raise ValueError(
                "Data Hub is disabled"
            )

        if data_hub.id is None:
            raise ValueError(
                "Data Hub id is required"
            )

        # =================================================
        # 3. Resolve Data Hub provider master data
        # =================================================

        provider_config = (
            await self.data_hub_provider_repository
            .get_by_id(
                data_hub.data_hub_provider_id,
            )
        )

        if provider_config is None:
            raise ValueError(
                "Data Hub provider not found"
            )

        if not provider_config.enabled:
            raise ValueError(
                "Data Hub provider is disabled"
            )

        # =================================================
        # 4. Load discovery checkpoint
        # =================================================

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

        # =================================================
        # 5. Build provider-neutral SourceReference
        # =================================================

        source_metadata = dict(
            data_hub.configuration
            or {}
        )

        # scope_data chỉ bổ sung/override phạm vi
        # của ingestion job.
        #
        # Discovery core không hiểu site_id,
        # folder_id, bucket, prefix...
        if job.scope_data:
            source_metadata.update(
                job.scope_data
            )

        source = SourceReference(
            provider=provider_config.provider,
            identifier=str(data_hub.id),
            metadata=source_metadata,
        )

        # =================================================
        # 6. Resolve actual provider
        # =================================================

        provider = (
            self.provider_resolver.resolve(
                provider=provider_config.provider,
                configuration=(
                    data_hub.configuration
                ),
            )
        )

        # =================================================
        # 7. Discover exactly one batch/page
        # =================================================

        page = await provider.discovery.discover(
            source=source,
            cursor=cursor,
            limit=request.batch_size,
        )

        discovered_files = (
            page.items
        )

        # Provider có thể move cursor nhưng batch này
        # không có file, ví dụ chỉ gặp folder.
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

        # =================================================
        # 8. Bulk load existing documents
        # =================================================

        external_file_ids = [
            item.external_file_id
            for item in discovered_files
        ]

        existing_documents = (
            await self.document_repository
            .get_by_external_file_ids(
                data_hub_id=data_hub.id,
                external_file_ids=(
                    external_file_ids
                ),
            )
        )

        result_items: list[
            DiscoveryItem
        ] = []

        states_to_dispatch: list[
            IngestionDocumentState
        ] = []

        # =================================================
        # 9. Upsert Documents + per-job state
        # =================================================

        for discovered_file in discovered_files:

            document = (
                existing_documents.get(
                    discovered_file.external_file_id
                )
            )

            if document is None:

                document = Document(
                    id=None,
                    data_hub_id=data_hub.id,
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

            # ---------------------------------------------
            # State của document trong ingestion job
            # ---------------------------------------------

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

                state = (
                    await self.ingestion_document_state_repository
                    .create(
                        state,
                    )
                )

            # PENDING nghĩa là chưa đảm bảo đã được
            # đưa sang Download queue.
            #
            # Nếu lần trước DB commit thành công nhưng
            # publish queue fail, retry sẽ publish lại.
            if (
                state.status
                == IngestionDocumentStatus.PENDING
            ):
                states_to_dispatch.append(
                    state
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

        # =================================================
        # 10. Save Discovery checkpoint
        # =================================================

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

        # Documents + state + checkpoint phải tồn tại
        # trước khi Download worker nhìn thấy message.
        await self.uow.commit()

        # =================================================
        # 11. Dispatch Download work
        # =================================================

        for state in states_to_dispatch:

            await self.download_dispatcher.dispatch(
                ingestion_job_id=(
                    request.ingestion_job_id
                ),
                document_id=state.document_id,
            )

            # Nếu publish thành công thì mark QUEUED.
            #
            # Nếu process chết trước commit cuối,
            # retry có thể publish duplicate.
            # Downstream phải idempotent.
            state.status = (
                IngestionDocumentStatus.QUEUED
            )

            await (
                self.ingestion_document_state_repository
                .update(
                    state,
                )
            )

        if states_to_dispatch:
            await self.uow.commit()

        # =================================================
        # 12. Return this batch
        # =================================================

        return DiscoverBatchResponse(
            ingestion_job_id=(
                request.ingestion_job_id
            ),
            items=result_items,
            has_more=page.has_more,
        )
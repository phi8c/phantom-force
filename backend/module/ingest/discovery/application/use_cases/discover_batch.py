from module.ingest.discovery.application.dtos.requests.discover_batch_request import (
    DiscoverBatchRequest,
)

from module.ingest.discovery.application.dtos.responses.discover_batch_response import (
    DiscoverBatchResponse,
    DiscoveryItem,
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
        ingestion_job_reader,
        data_hub_reader,
        provider_resolver,
        document_repository,
        ingestion_document_state_repository,
        discovery_state_repository,
        download_dispatcher,
        uow,
    ):
        self.ingestion_job_reader = ingestion_job_reader
        self.data_hub_reader = data_hub_reader
        self.provider_resolver = provider_resolver

        self.document_repository = document_repository
        self.ingestion_document_state_repository = (
            ingestion_document_state_repository
        )

        self.discovery_state_repository = (
            discovery_state_repository
        )

        self.download_dispatcher = download_dispatcher
        self.uow = uow

    async def execute(
        self,
        request: DiscoverBatchRequest,
    ) -> DiscoverBatchResponse:

        # -------------------------------------------------
        # 1. Load ingestion job
        # -------------------------------------------------

        job = await self.ingestion_job_reader.get_by_id(
            request.ingestion_job_id,
        )

        if job is None:
            raise ValueError(
                "Ingestion job not found"
            )

        if job.knowledge_space_id is None:
            raise ValueError(
                "Ingestion job has no knowledge space"
            )

        # -------------------------------------------------
        # 2. Resolve Data Hub của Knowledge Space
        # -------------------------------------------------

        data_hub = await self.data_hub_reader.get_enabled_by_knowledge_space(
            job.knowledge_space_id,
        )

        if data_hub is None:
            raise ValueError(
                "No enabled Data Hub found for knowledge space"
            )

        # -------------------------------------------------
        # 3. Load discovery checkpoint
        # -------------------------------------------------

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
                ingestion_job_id=request.ingestion_job_id,
                items=[],
                has_more=False,
            )

        cursor = (
            discovery_state.cursor
            if discovery_state is not None
            else None
        )

        # -------------------------------------------------
        # 4. Resolve provider
        # -------------------------------------------------

        provider = self.provider_resolver.resolve(
            provider_code=data_hub.provider_code,
            configuration=data_hub.configuration,
        )

        # -------------------------------------------------
        # 5. Discovery một page/batch
        # -------------------------------------------------

        page = await provider.discovery.discover(
            scope_type=job.scope_type,
            scope_data=job.scope_data,
            cursor=cursor,
            limit=request.batch_size,
        )

        discovered_files = page.items

        if not discovered_files:
            await self.discovery_state_repository.complete(
                ingestion_job_id=request.ingestion_job_id,
            )

            await self.uow.commit()

            return DiscoverBatchResponse(
                ingestion_job_id=request.ingestion_job_id,
                items=[],
                has_more=False,
            )

        # -------------------------------------------------
        # 6. Query documents hiện có theo batch
        # -------------------------------------------------

        external_file_ids = [
            item.external_file_id
            for item in discovered_files
        ]

        existing_documents = (
            await self.document_repository
            .get_by_external_file_ids(
                data_hub_id=data_hub.id,
                external_file_ids=external_file_ids,
            )
        )

        result_items: list[DiscoveryItem] = []
        document_ids_to_dispatch = []

        # -------------------------------------------------
        # 7. Upsert documents + ingestion states
        # -------------------------------------------------

        for discovered_file in discovered_files:

            document = existing_documents.get(
                discovered_file.external_file_id,
            )

            if document is None:

                document = Document(
                    id=None,
                    data_hub_id=data_hub.id,
                    external_file_id=(
                        discovered_file.external_file_id
                    ),
                    file_name=discovered_file.file_name,
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

                document = await self.document_repository.create(
                    document,
                )

            else:
                # Metadata của provider có thể thay đổi
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

            # ---------------------------------------------
            # State của document trong ingestion job này
            # ---------------------------------------------

            state = (
                await self.ingestion_document_state_repository
                .get_by_document_and_ingestion_job(
                    document_id=document.id,
                    ingestion_job_id=request.ingestion_job_id,
                )
            )

            if state is None:

                state = IngestionDocumentState(
                    document_id=document.id,
                    ingestion_job_id=request.ingestion_job_id,
                    status=IngestionDocumentStatus.PENDING,
                    created_at=None,
                    updated_at=None,
                )

                await self.ingestion_document_state_repository.create(
                    state,
                )

                document_ids_to_dispatch.append(
                    document.id,
                )

            result_items.append(
                DiscoveryItem(
                    document_id=document.id,
                    external_file_id=(
                        discovered_file.external_file_id
                    ),
                    file_name=(
                        discovered_file.file_name
                    ),
                )
            )

        # -------------------------------------------------
        # 8. Save checkpoint
        # -------------------------------------------------

        await self.discovery_state_repository.save_progress(
            ingestion_job_id=request.ingestion_job_id,
            cursor=page.next_cursor,
            discovered_count=len(discovered_files),
            completed=not page.has_more,
        )

        # DB trước
        await self.uow.commit()

        # -------------------------------------------------
        # 9. Dispatch Download
        # -------------------------------------------------

        for document_id in document_ids_to_dispatch:
            await self.download_dispatcher.dispatch(
                ingestion_job_id=request.ingestion_job_id,
                document_id=document_id,
            )

        return DiscoverBatchResponse(
            ingestion_job_id=request.ingestion_job_id,
            items=result_items,
            has_more=page.has_more,
        )
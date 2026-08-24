from uuid import UUID

from app.domain.entities.ingestion_run import (
    IngestionRun,
)

from app.domain.enums.ingestion_status import (
    IngestionStatus,
)

from app.domain.repositories.ingestion_run_repository import (
    IngestionRunRepository,
)

from app.domain.unit_of_work.unit_of_work import (
    UnitOfWork,
)

from datetime import datetime
from datetime import timezone

from app.domain.entities.document import (
    Document,
)

from app.domain.entities.ingestion_run import (
    IngestionRun,
)

from app.domain.enums.ingestion_status import (
    IngestionStatus,
)



class StartIngestionUseCase:

    def __init__(
        self,
        repository,
        document_repository,
        document_source,
        download_dispatcher,
        uow,
    ):
        self.repository = repository

        self.document_repository = (
            document_repository
        )

        self.document_source = (
            document_source
        )

        self.download_dispatcher = (
            download_dispatcher
        )

        self.uow = uow

    async def execute(
    self,
    source_id,
    trigger_type,
    scope_type,
    is_build_graph,
    configuration,
    site_id=None,
    drive_id=None,
    folder_id=None,
    file_id=None,
):

        ingestion_run = IngestionRun(
            id=None,
            source_id=source_id,
            trigger_type=trigger_type,
            scope_type=scope_type,
            scope_data={
                "site_id": site_id,
                "drive_id": drive_id,
                "folder_id": folder_id,
                "file_id": file_id,
            },
            configuration=(configuration.model_dump()),
            status=IngestionStatus.PENDING,
            is_build_graph=is_build_graph,
            total_files=0,
            completed_files=0,
            failed_files=0,
            started_at=None,
            finished_at=None,
            created_at=None,
        )

        created_run = await (
            self.repository.create(
                ingestion_run,
            )
        )

        files = await (
            self.document_source.discover_files(
                created_run,
            )
        )

        documents = []

        for file in files:

            existing = await (
                self.document_repository
                .get_by_external_file_id(
                    source_id,
                    file.external_file_id,
                )
            )

            if existing:

                documents.append(
                    existing,
                )

                continue
            
            provider_metadata = dict(
                file.provider_metadata or {}
            )

            provider_metadata["file_id"] = (
                file.external_file_id
            )


            document = Document(
                id=None,
                source_id=source_id,
                external_file_id=(
                    file.external_file_id
                ),
                provider_metadata=(
                    file.provider_metadata
                ),
                file_name=file.file_name,
                department=None,
                owner_role=None,
                security_level=None,
                document_type=None,
                source_file_url=(
                    file.source_file_url
                ),
                file_extension=(
                    file.file_extension
                ),
                file_size_bytes=(
                    file.file_size_bytes
                ),
                content_hash=None,
                processing_status=(
                    "PENDING_DOWNLOAD"
                ),
                processing_error=None,
                temp_file_path=None,
                original_file_path=(
                    file.original_file_path
                ),
                last_modified_at=(
                    file.last_modified_at
                ),
                last_ingested_at=None,
                created_at=datetime.now(
                    timezone.utc,
                ),
                updated_at=None,
            )

            document = await (
                self.document_repository.create(
                    document,
                )
            )

            documents.append(
                document,
            )

        created_run.total_files = (
            len(documents)
        )

        await self.uow.commit()

        for document in documents:

            await (
                self.download_dispatcher.dispatch(
                    document.id,
                )
            )

        return created_run
from app.domain.entities.document import (
Document,
)

from app.domain.entities.document_processing_task import (
DocumentProcessingTask,
)

from app.domain.enums.ingestion_status import (
IngestionStatus,
)

from app.domain.enums.task_status import (
TaskStatus,
)

from app.domain.enums.task_type import (
TaskType,
)

from app.domain.ports.messaging.message_bus import (
MessageBus,
)

class RegisterDocumentsUseCase:


    def __init__(
        self,
        document_repository,
        task_repository,
        message_bus: MessageBus,
        uow,
    ):
        self.document_repository = (
            document_repository
        )

        self.task_repository = (
            task_repository
        )

        self.message_bus = (
            message_bus
        )

        self.uow = uow

    async def execute(
        self,
        source_id,
        files,
    ):

        existing_documents = await (
            self.document_repository
            .get_by_external_file_ids(
                source_id=source_id,
                external_file_ids=[
                    file.external_file_id
                    for file in files
                ],
            )
        )

        created_count = 0

        created_task_ids: list[str] = []

        for file in files:

            existing = (
                existing_documents.get(
                    file.external_file_id,
                )
            )

            # =====================
            # FILE ĐÃ TỒN TẠI
            # =====================

            if existing:

                if (
                    existing.last_modified_at
                    == file.last_modified_at
                ):
                    continue

                existing.file_name = (
                    file.file_name
                )

                existing.file_extension = (
                    file.file_extension
                )

                existing.file_size_bytes = (
                    file.file_size_bytes
                )

                existing.source_file_url = (
                    file.source_file_url
                )

                existing.provider_metadata = (
                    file.provider_metadata
                )

                existing.last_modified_at = (
                    file.last_modified_at
                )

                existing.processing_status = (
                    IngestionStatus.PENDING.value
                )

                existing.processing_error = (
                    None
                )

                existing.last_ingested_at = (
                    None
                )

                await (
                    self.document_repository.update(
                        existing,
                    )
                )

                document = existing

            # =====================
            # FILE MỚI
            # =====================

            else:

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
                        IngestionStatus.PENDING.value
                    ),

                    processing_error=None,

                    temp_file_path=None,

                    last_modified_at=(
                        file.last_modified_at
                    ),

                    last_ingested_at=None,

                    created_at=None,

                    updated_at=None,
                )

                document = await (
                    self.document_repository.create(
                        document,
                    )
                )

                created_count += 1

            # =====================
            # DOWNLOAD TASK
            # =====================

            task = (
                DocumentProcessingTask(
                    document_id=document.id,
                    task_type=TaskType.DOWNLOAD,
                    status=TaskStatus.PENDING,
                )
            )

            task = await (
                self.task_repository.create(
                    task,
                )
            )

            created_task_ids.append(
                str(task.id)
            )

        # =====================
        # COMMIT DB
        # =====================

        await self.uow.commit()

        # =====================
        # PUSH QUEUE
        # =====================

        for task_id in created_task_ids:

            await (
                self.message_bus
                .publish_download_task(
                    task_id,
                )
            )

        return {
            "created_documents":
                created_count,

            "created_tasks":
                len(
                    created_task_ids,
                ),
        }
    

from datetime import datetime
from datetime import timezone
from uuid import UUID

from module.ingest.download.domain.contracts.document_source import (
    DocumentSource,
)

from module.ingest.download.domain.contracts.download_task_repository import (
    DownloadTaskRepository,
)

from module.ingest.download.domain.contracts.extraction_task_scheduler import (
    ExtractionTaskScheduler,
)

from module.ingest.download.domain.contracts.object_storage import (
    ObjectStorage,
)

from module.ingest.download.domain.contracts.storage_asset_repository import (
    StorageAsset,
    StorageAssetRepository,
)

from module.ingest.download.domain.contracts.unit_of_work import (
    UnitOfWork,
)

from module.ingest.download.domain.enums.task_status import (
    TaskStatus,
)


class DownloadFileUseCase:

    def __init__(
        self,
        task_repository: DownloadTaskRepository,
        document_source: DocumentSource,
        object_storage: ObjectStorage,
        storage_asset_repository: StorageAssetRepository,
        extraction_task_scheduler: ExtractionTaskScheduler,
        uow: UnitOfWork,
        max_attempts: int = 3,
    ):
        self.task_repository = task_repository
        self.document_source = document_source
        self.object_storage = object_storage
        self.storage_asset_repository = (
            storage_asset_repository
        )
        self.extraction_task_scheduler = (
            extraction_task_scheduler
        )
        self.uow = uow
        self.max_attempts = max_attempts

    async def execute(
        self,
        task_id: UUID,
    ) -> None:

        task = await self.task_repository.get_by_id(
            task_id,
        )

        if task is None:
            raise ValueError(
                "Download task not found"
            )

        if (
            task.status
            != TaskStatus.PROCESSING
        ):
            raise ValueError(
                "Download task must be PROCESSING"
            )

        try:

            source = await self.document_source.open(
                task.document_id,
            )

            storage_path = self._build_storage_path(
                ingestion_job_id=(
                    task.ingestion_job_id
                ),
                document_id=task.document_id,
                file_name=source.file_name,
            )

            stored_object = (
                await self.object_storage.upload_stream(
                    path=storage_path,
                    content=source.content,
                    content_type=(
                        source.content_type
                    ),
                )
            )

            await self.storage_asset_repository.create(
                StorageAsset(
                    id=None,
                    document_id=task.document_id,
                    storage_provider_id=(
                        stored_object.provider_id
                    ),
                    asset_type="SOURCE",
                    storage_path=(
                        stored_object.path
                    ),
                    content_type=(
                        stored_object.content_type
                        or source.content_type
                    ),
                    size_bytes=(
                        stored_object.size_bytes
                        or source.size_bytes
                    ),
                )
            )

            task.status = (
                TaskStatus.COMPLETED
            )

            task.claimed_by = None
            task.lease_until = None
            task.error = None

            task.completed_at = datetime.now(
                timezone.utc,
            )

            await self.task_repository.update(
                task,
            )

            await (
                self.extraction_task_scheduler
                .ensure_ready_task(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                )
            )

            await self.uow.commit()

        except Exception as exc:

            await self.uow.rollback()

            task = await self.task_repository.get_by_id(
                task_id,
            )

            if task is not None:

                if (
                    task.attempt_count
                    >= self.max_attempts
                ):
                    task.status = (
                        TaskStatus.FAILED
                    )
                else:
                    task.status = (
                        TaskStatus.READY
                    )

                task.claimed_by = None
                task.lease_until = None
                task.error = str(exc)

                await self.task_repository.update(
                    task,
                )

                await self.uow.commit()

            raise

    @staticmethod
    def _build_storage_path(
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        file_name: str,
    ) -> str:

        safe_name = (
            file_name
            .replace("/", "_")
            .replace("\\", "_")
        )

        return (
            f"ingest/"
            f"{ingestion_job_id}/"
            f"{document_id}/"
            f"{safe_name}"
        )

import json
import tempfile
from collections.abc import AsyncIterator
from datetime import datetime
from datetime import timezone
from pathlib import Path
from uuid import UUID

from module.ingest.extraction.domain.contracts.chunking_task_scheduler import (
    ChunkingTaskScheduler,
)
from module.ingest.extraction.domain.contracts.extraction_engine_resolver import (
    ExtractionEngineResolver,
)
from module.ingest.extraction.domain.contracts.extraction_task_repository import (
    ExtractionTaskRepository,
)
from module.ingest.extraction.domain.contracts.object_storage import (
    ObjectStorage,
)
from module.ingest.extraction.domain.contracts.source_asset_reader import (
    SourceAssetReader,
)
from module.ingest.extraction.domain.contracts.storage_asset_repository import (
    StorageAsset,
    StorageAssetRepository,
)
from module.ingest.extraction.domain.contracts.unit_of_work import (
    UnitOfWork,
)
from module.ingest.extraction.domain.enums.task_status import (
    TaskStatus,
)


class ExtractDocumentUseCase:

    def __init__(
        self,
        task_repository: ExtractionTaskRepository,
        source_asset_reader: SourceAssetReader,
        extraction_engine_resolver: ExtractionEngineResolver,
        object_storage: ObjectStorage,
        storage_asset_repository: StorageAssetRepository,
        chunking_task_scheduler: ChunkingTaskScheduler,
        uow: UnitOfWork,
        max_attempts: int = 3,
    ):
        self.task_repository = task_repository
        self.source_asset_reader = source_asset_reader
        self.extraction_engine_resolver = (
            extraction_engine_resolver
        )
        self.object_storage = object_storage
        self.storage_asset_repository = (
            storage_asset_repository
        )
        self.chunking_task_scheduler = (
            chunking_task_scheduler
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
                "Extraction task not found"
            )

        if task.status != TaskStatus.PROCESSING:
            raise ValueError(
                "Extraction task must be PROCESSING"
            )

        temp_path: Path | None = None

        try:
            existing_asset = (
                await self.storage_asset_repository
                .get_by_document_and_type(
                    document_id=task.document_id,
                    asset_type="EXTRACTED",
                )
            )

            if existing_asset is None:
                source_asset = (
                    await self.source_asset_reader
                    .open_source(
                        task.document_id,
                    )
                )

                temp_path = await self._write_temp_file(
                    source_asset.content,
                    suffix=self._suffix_for(
                        source_asset.file_name
                    ),
                )

                extraction_engine = (
                    await self.extraction_engine_resolver
                    .resolve_for_job(
                        task.ingestion_job_id,
                    )
                )

                extraction_result = (
                    await extraction_engine.extract(
                        temp_path,
                    )
                )

                storage_path = (
                    self._build_storage_path(
                        ingestion_job_id=(
                            task.ingestion_job_id
                        ),
                        document_id=task.document_id,
                    )
                )

                stored_object = (
                    await self.object_storage
                    .upload_stream(
                        path=storage_path,
                        content=(
                            self._json_stream(
                                extraction_result.content
                            )
                        ),
                        content_type=(
                            extraction_result
                            .content_type
                        ),
                    )
                )

                existing_asset = (
                    await self.storage_asset_repository
                    .create(
                        StorageAsset(
                            id=None,
                            document_id=(
                                task.document_id
                            ),
                            storage_provider_id=(
                                stored_object
                                .provider_id
                            ),
                            asset_type="EXTRACTED",
                            storage_path=(
                                stored_object.path
                            ),
                            content_type=(
                                stored_object
                                .content_type
                                or extraction_result
                                .content_type
                            ),
                            size_bytes=(
                                stored_object
                                .size_bytes
                            ),
                        )
                    )
                )

            if existing_asset.id is None:
                raise ValueError(
                    "Extracted asset id was not generated"
                )

            await (
                self.chunking_task_scheduler
                .ensure_ready_task(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                    extracted_asset_id=(
                        existing_asset.id
                    ),
                )
            )

            task.status = TaskStatus.COMPLETED
            task.claimed_by = None
            task.lease_until = None
            task.error = None
            task.completed_at = datetime.now(
                timezone.utc,
            )

            await self.task_repository.update(
                task,
            )

            await self.uow.commit()

            await (
                self.chunking_task_scheduler
                .dispatch_job(
                    task.ingestion_job_id,
                )
            )

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
                    task.status = TaskStatus.FAILED
                else:
                    task.status = TaskStatus.READY

                task.claimed_by = None
                task.lease_until = None
                task.error = str(exc)

                await self.task_repository.update(
                    task,
                )

                await self.uow.commit()

            raise

        finally:
            if temp_path is not None:
                temp_path.unlink(
                    missing_ok=True,
                )

    @staticmethod
    async def _write_temp_file(
        content: AsyncIterator[bytes],
        *,
        suffix: str,
    ) -> Path:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_path = Path(
                temp_file.name,
            )

            async for chunk in content:
                temp_file.write(
                    chunk,
                )

        return temp_path

    @staticmethod
    async def _json_stream(
        content: object,
    ) -> AsyncIterator[bytes]:
        encoder = json.JSONEncoder(
            ensure_ascii=False,
        )

        for chunk in encoder.iterencode(
            content,
        ):
            yield chunk.encode(
                "utf-8",
            )

    @staticmethod
    def _build_storage_path(
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> str:

        return (
            f"ingest/"
            f"{ingestion_job_id}/"
            f"{document_id}/"
            f"extracted.json"
        )

    @staticmethod
    def _suffix_for(
        file_name: str,
    ) -> str:

        path = Path(
            file_name,
        )

        return path.suffix or ".bin"

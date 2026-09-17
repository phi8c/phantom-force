import json
import logging
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
from module.ingest.orchestration.application.services import (
    NoOpOrchestrationProgressService,
)
from module.ingest.orchestration.application.services import (
    OrchestrationProgressService,
)
from module.ingest.orchestration.domain.enums import IngestionStage


logger = logging.getLogger(__name__)


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
        orchestration_progress_service: (
            OrchestrationProgressService
            | NoOpOrchestrationProgressService
            | None
        ) = None,
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
        self.orchestration_progress_service = (
            orchestration_progress_service
            or NoOpOrchestrationProgressService()
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
            logger.info(
                "extraction usecase_start task_id=%s job_id=%s document_id=%s",
                task_id,
                task.ingestion_job_id,
                task.document_id,
            )

            storage_path = (
                self._build_storage_path(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                )
            )

            existing_asset = (
                await self.storage_asset_repository
                .get_by_document_type_and_path(
                    document_id=task.document_id,
                    asset_type="EXTRACTED",
                    storage_path=storage_path,
                )
            )

            if existing_asset is None:
                logger.info(
                    "extraction source_open document_id=%s",
                    task.document_id,
                )
                source_asset = (
                    await self.source_asset_reader
                    .open_source(
                        task.document_id,
                    )
                )
                print(
                    "\n===== EXTRACTION SOURCE ASSET START =====",
                    flush=True,
                )
                print(
                    f"task_id={task_id}",
                    flush=True,
                )
                print(
                    f"job_id={task.ingestion_job_id}",
                    flush=True,
                )
                print(
                    f"document_id={task.document_id}",
                    flush=True,
                )
                print(
                    f"file_name={source_asset.file_name}",
                    flush=True,
                )
                print(
                    f"content_type={source_asset.content_type}",
                    flush=True,
                )
                print(
                    f"declared_size_bytes={source_asset.size_bytes}",
                    flush=True,
                )
                print(
                    "===== EXTRACTION SOURCE ASSET END =====\n",
                    flush=True,
                )

                temp_path = await self._write_temp_file(
                    source_asset.content,
                    suffix=self._suffix_for(
                        source_asset.file_name
                    ),
                )
                print(
                    "\n===== EXTRACTION TEMP FILE START =====",
                    flush=True,
                )
                print(
                    f"task_id={task_id}",
                    flush=True,
                )
                print(
                    f"job_id={task.ingestion_job_id}",
                    flush=True,
                )
                print(
                    f"document_id={task.document_id}",
                    flush=True,
                )
                print(
                    f"temp_path={temp_path}",
                    flush=True,
                )
                print(
                    f"temp_suffix={temp_path.suffix}",
                    flush=True,
                )
                print(
                    f"temp_size_bytes={temp_path.stat().st_size}",
                    flush=True,
                )
                print(
                    "===== EXTRACTION TEMP FILE END =====\n",
                    flush=True,
                )

                extraction_engine = (
                    await self.extraction_engine_resolver
                    .resolve_for_job(
                        task.ingestion_job_id,
                    )
                )

                logger.info(
                    "extraction engine_start task_id=%s job_id=%s",
                    task_id,
                    task.ingestion_job_id,
                )

                extraction_result = (
                    await extraction_engine.extract(
                        temp_path,
                    )
                )

                logger.info(
                    "extraction engine_done task_id=%s content_type=%s",
                    task_id,
                    extraction_result.content_type,
                )
                print(
                    "\n===== EXTRACTION RAW RESULT START =====",
                    flush=True,
                )
                print(
                    f"task_id={task_id}",
                    flush=True,
                )
                print(
                    f"job_id={task.ingestion_job_id}",
                    flush=True,
                )
                print(
                    f"document_id={task.document_id}",
                    flush=True,
                )
                print(
                    f"content_type={extraction_result.content_type}",
                    flush=True,
                )
                print(
                    extraction_result.content,
                    flush=True,
                )
                print(
                    "===== EXTRACTION RAW RESULT END =====\n",
                    flush=True,
                )

                if (
                    extraction_result.content
                    is None
                ):
                    raise ValueError(
                        "Extraction result content is required"
                    )

                if not extraction_result.content_type:
                    raise ValueError(
                        "Extraction result content_type is required"
                    )

                existing_asset = (
                    await self.storage_asset_repository
                    .get_by_document_type_and_path(
                        document_id=task.document_id,
                        asset_type="EXTRACTED",
                        storage_path=storage_path,
                    )
                )

                if existing_asset is None:
                    output_summary = _summarize_extraction_output(
                        extraction_result.content,
                    )
                    logger.info(
                        "extraction output_summary document_id=%s "
                        "content_type=%s top_level_keys=%s sections_count=%s",
                        task.document_id,
                        output_summary["content_type"],
                        output_summary["top_level_keys"],
                        output_summary["sections_count"],
                    )
                    print(
                        "extraction output_summary "
                        f"document_id={task.document_id} "
                        f"content_type={output_summary['content_type']} "
                        f"top_level_keys={output_summary['top_level_keys']} "
                        f"sections_count={output_summary['sections_count']}",
                        flush=True,
                    )

                    logger.info(
                        "extraction upload_start task_id=%s path=%s",
                        task_id,
                        storage_path,
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

                    logger.info(
                        "extraction upload_done task_id=%s path=%s",
                        task_id,
                        stored_object.path,
                    )

                    if stored_object.path != storage_path:
                        raise ValueError(
                            "Stored extracted asset path mismatch"
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
                    logger.info(
                        "extraction asset_saved task_id=%s asset_id=%s",
                        task_id,
                        existing_asset.id,
                    )
            else:
                logger.info(
                    "extraction asset_reused task_id=%s asset_id=%s path=%s",
                    task_id,
                    existing_asset.id,
                    existing_asset.storage_path,
                )

            if existing_asset.id is None:
                raise ValueError(
                    "Extracted asset id was not generated"
                )

            if (
                existing_asset.asset_type != "EXTRACTED"
                or existing_asset.document_id
                != task.document_id
                or existing_asset.storage_path
                != storage_path
            ):
                raise ValueError(
                    "Extracted asset does not match task"
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

            logger.info(
                "extraction schedule_chunking task_id=%s asset_id=%s",
                task_id,
                existing_asset.id,
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

            await (
                self.orchestration_progress_service
                .mark_stage_completed(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                    stage=IngestionStage.EXTRACTION,
                )
            )

            await (
                self.orchestration_progress_service
                .mark_stage_ready(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                    stage=IngestionStage.CHUNKING,
                )
            )

            logger.info(
                "extraction commit task_id=%s",
                task_id,
            )
            await self.uow.commit()

            logger.info(
                "extraction dispatch_chunking job_id=%s",
                task.ingestion_job_id,
            )
            await (
                self.chunking_task_scheduler
                .dispatch_job(
                    task.ingestion_job_id,
                )
            )

        except Exception as exc:
            logger.exception(
                "extraction failed task_id=%s error=%s",
                task_id,
                exc,
            )
            print(
                "extraction failed "
                f"task_id={task_id} "
                f"error={exc}",
                flush=True,
            )
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

                if task.status == TaskStatus.FAILED:
                    await (
                        self.orchestration_progress_service
                        .mark_stage_failed(
                            ingestion_job_id=(
                                task.ingestion_job_id
                            ),
                            document_id=task.document_id,
                            stage=IngestionStage.EXTRACTION,
                            error=str(exc),
                        )
                    )
                else:
                    await (
                        self.orchestration_progress_service
                        .mark_stage_ready(
                            ingestion_job_id=(
                                task.ingestion_job_id
                            ),
                            document_id=task.document_id,
                            stage=IngestionStage.EXTRACTION,
                        )
                    )

                await self.uow.commit()

                logger.info(
                    "extraction retry_state task_id=%s status=%s",
                    task_id,
                    task.status.value,
                )

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
            total_bytes = 0
            chunk_count = 0
            preview = bytearray()

            async for chunk in content:
                chunk_count += 1
                chunk_size = len(
                    chunk,
                )
                total_bytes += chunk_size

                if len(
                    preview,
                ) < 512:
                    preview.extend(
                        chunk[
                            : 512 - len(
                                preview,
                            )
                        ]
                    )

                print(
                    "extraction source_stream chunk "
                    f"chunk_index={chunk_count} "
                    f"chunk_bytes={chunk_size} "
                    f"total_bytes={total_bytes}",
                    flush=True,
                )
                temp_file.write(
                    chunk,
                )

        print(
            "\n===== EXTRACTION SOURCE STREAM SUMMARY START =====",
            flush=True,
        )
        print(
            f"temp_path={temp_path}",
            flush=True,
        )
        print(
            f"suffix={suffix}",
            flush=True,
        )
        print(
            f"chunks={chunk_count}",
            flush=True,
        )
        print(
            f"total_bytes={total_bytes}",
            flush=True,
        )
        print(
            f"preview_hex={preview.hex()}",
            flush=True,
        )
        print(
            "preview_text="
            f"{preview.decode('utf-8', errors='replace')}",
            flush=True,
        )
        print(
            "===== EXTRACTION SOURCE STREAM SUMMARY END =====\n",
            flush=True,
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


def _summarize_extraction_output(
    content: object,
) -> dict:

    parsed_content = _parse_json_like_content(
        content,
    )

    top_level_keys = []
    sections = []

    if isinstance(
        parsed_content,
        dict,
    ):
        top_level_keys = list(
            parsed_content.keys(),
        )
        raw_sections = parsed_content.get(
            "sections",
            [],
        )

        if isinstance(
            raw_sections,
            list,
        ):
            sections = raw_sections

    return {
        "content_type": type(content).__name__,
        "top_level_keys": top_level_keys,
        "sections_count": _count_sections(
            sections,
        ),
    }


def _parse_json_like_content(
    content: object,
) -> object:

    if isinstance(
        content,
        bytes,
    ):
        try:
            content = content.decode(
                "utf-8",
            )
        except UnicodeDecodeError:
            return content

    if isinstance(
        content,
        str,
    ):
        try:
            return json.loads(
                content,
            )
        except json.JSONDecodeError:
            return content

    return content


def _count_sections(
    sections: list,
) -> int:

    count = 0
    stack = list(
        reversed(
            sections,
        )
    )

    while stack:
        section = stack.pop()

        if not isinstance(
            section,
            dict,
        ):
            continue

        count += 1

        children = section.get(
            "children",
            [],
        )

        if isinstance(
            children,
            list,
        ):
            stack.extend(
                reversed(
                    children,
                )
            )

    return count

import os
import logging
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path
from uuid import UUID

from module.ingest.chunking.domain.contracts.chunk_batch_writer import (
    ChunkBatchWriter,
)
from module.ingest.chunking.domain.contracts.chunking_engine import (
    ExtractedDocument,
)
from module.ingest.chunking.domain.contracts.chunking_engine_resolver import (
    ChunkingEngineResolver,
)
from module.ingest.chunking.domain.contracts.chunking_task_repository import (
    ChunkingTaskRepository,
)
from module.ingest.chunking.domain.contracts.downstream_task_scheduler import (
    DownstreamTaskScheduler,
)
from module.ingest.chunking.domain.contracts.extracted_asset_reader import (
    ExtractedAssetReader,
)
from module.ingest.chunking.domain.contracts.unit_of_work import (
    UnitOfWork,
)
from module.ingest.chunking.domain.enums.task_status import (
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


class ChunkDocumentUseCase:

    def __init__(
        self,
        task_repository: ChunkingTaskRepository,
        extracted_asset_reader: ExtractedAssetReader,
        chunking_engine_resolver: ChunkingEngineResolver,
        chunk_batch_writer: ChunkBatchWriter,
        downstream_task_scheduler: DownstreamTaskScheduler,
        uow: UnitOfWork,
        orchestration_progress_service: (
            OrchestrationProgressService
            | NoOpOrchestrationProgressService
            | None
        ) = None,
        max_attempts: int = 3,
    ):
        self.task_repository = task_repository
        self.extracted_asset_reader = (
            extracted_asset_reader
        )
        self.chunking_engine_resolver = (
            chunking_engine_resolver
        )
        self.chunk_batch_writer = chunk_batch_writer
        self.downstream_task_scheduler = (
            downstream_task_scheduler
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
                "Chunking task not found"
            )

        if task.status != TaskStatus.PROCESSING:
            raise ValueError(
                "Chunking task must be PROCESSING"
            )

        try:
            logger.info(
                "chunking usecase_start task_id=%s job_id=%s document_id=%s",
                task_id,
                task.ingestion_job_id,
                task.document_id,
            )

            existing_batch = (
                await self.chunk_batch_writer
                .get_by_job_and_document(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                )
            )

            if existing_batch is None:
                logger.info(
                    "chunking extracted_open task_id=%s",
                    task_id,
                )
                extracted_asset = (
                    await self.extracted_asset_reader
                    .open_extracted(
                        ingestion_job_id=(
                            task.ingestion_job_id
                        ),
                        document_id=(
                            task.document_id
                        ),
                    )
                )

                extracted_path = (
                    await self._write_temp_file(
                        extracted_asset.content,
                    )
                )

                try:
                    chunking_engine = (
                        await self.chunking_engine_resolver
                        .resolve_for_job(
                            task.ingestion_job_id,
                        )
                    )

                    logger.info(
                        "chunking engine_start task_id=%s",
                        task_id,
                    )
                    chunks = list(
                        chunking_engine.chunk(
                            ExtractedDocument(
                                document_id=task.document_id,
                                content_path=extracted_path,
                            )
                        )
                    )

                    logger.info(
                        "chunking engine_done task_id=%s chunks=%s",
                        task_id,
                        len(chunks),
                    )

                    batch = await (
                        self.chunk_batch_writer
                        .create_with_chunks(
                            ingestion_job_id=(
                                task.ingestion_job_id
                            ),
                            document_id=task.document_id,
                            chunks=chunks,
                        )
                    )
                    logger.info(
                        "chunking batch_saved task_id=%s batch_id=%s",
                        task_id,
                        batch.id,
                    )

                finally:
                    try:
                        os.unlink(
                            extracted_path,
                        )
                    except FileNotFoundError:
                        pass

            else:
                batch = existing_batch
                logger.info(
                    "chunking batch_reused task_id=%s batch_id=%s",
                    task_id,
                    batch.id,
                )

            logger.info(
                "chunking downstream_schedule task_id=%s batch_id=%s",
                task_id,
                batch.id,
            )
            signals = (
                await self.downstream_task_scheduler
                .schedule(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                    batch_id=batch.id,
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

            await (
                self.orchestration_progress_service
                .mark_stage_completed(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                    stage=IngestionStage.CHUNKING,
                )
            )

            await (
                self.orchestration_progress_service
                .mark_stage_ready(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                    stage=IngestionStage.EMBEDDING,
                )
            )

            if signals.classification_skipped:
                await (
                    self.orchestration_progress_service
                    .mark_stage_skipped(
                        ingestion_job_id=(
                            task.ingestion_job_id
                        ),
                        document_id=task.document_id,
                        stage=IngestionStage.CLASSIFICATION,
                    )
                )
            elif signals.dispatch_classification:
                await (
                    self.orchestration_progress_service
                    .mark_stage_ready(
                        ingestion_job_id=(
                            task.ingestion_job_id
                        ),
                        document_id=task.document_id,
                        stage=IngestionStage.CLASSIFICATION,
                    )
                )

            logger.info(
                "chunking commit task_id=%s",
                task_id,
            )
            await self.uow.commit()

            if signals.dispatch_embedding:
                logger.info(
                    "chunking dispatch_embedding job_id=%s",
                    task.ingestion_job_id,
                )
                await (
                    self.downstream_task_scheduler
                    .dispatch_embedding(
                        task.ingestion_job_id,
                    )
                )

            if signals.dispatch_classification:
                logger.info(
                    "chunking dispatch_classification job_id=%s",
                    task.ingestion_job_id,
                )
                await (
                    self.downstream_task_scheduler
                    .dispatch_classification(
                        task.ingestion_job_id,
                    )
                )

        except Exception as exc:
            logger.exception(
                "chunking failed task_id=%s error=%s",
                task_id,
                exc,
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
                            stage=IngestionStage.CHUNKING,
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
                            stage=IngestionStage.CHUNKING,
                        )
                    )

                await self.uow.commit()

                logger.info(
                    "chunking retry_state task_id=%s status=%s",
                    task_id,
                    task.status.value,
                )

            raise

    @staticmethod
    async def _write_temp_file(
        content,
    ) -> Path:

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".json",
        )

        temp_path = Path(
            temp_file.name,
        )

        try:
            with temp_file:
                async for chunk in content:
                    temp_file.write(
                        chunk,
                    )

        except Exception:
            try:
                os.unlink(
                    temp_path,
                )
            except FileNotFoundError:
                pass
            raise

        return temp_path

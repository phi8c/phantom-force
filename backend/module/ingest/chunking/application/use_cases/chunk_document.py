import json
from datetime import datetime
from datetime import timezone
from uuid import UUID

from module.ingest.chunking.domain.contracts.chunk_batch_writer import (
    ChunkBatchWriter,
)
from module.ingest.chunking.domain.contracts.chunking_engine import (
    ChunkingEngine,
    ExtractedDocument,
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


class ChunkDocumentUseCase:

    def __init__(
        self,
        task_repository: ChunkingTaskRepository,
        extracted_asset_reader: ExtractedAssetReader,
        chunking_engine: ChunkingEngine,
        chunk_batch_writer: ChunkBatchWriter,
        downstream_task_scheduler: DownstreamTaskScheduler,
        uow: UnitOfWork,
        max_attempts: int = 3,
    ):
        self.task_repository = task_repository
        self.extracted_asset_reader = (
            extracted_asset_reader
        )
        self.chunking_engine = chunking_engine
        self.chunk_batch_writer = chunk_batch_writer
        self.downstream_task_scheduler = (
            downstream_task_scheduler
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

                extracted_content = (
                    await self._read_json(
                        extracted_asset.content,
                    )
                )

                chunks = await self.chunking_engine.chunk(
                    ExtractedDocument(
                        document_id=task.document_id,
                        content=extracted_content,
                    )
                )

                batch = (
                    await self.chunk_batch_writer
                    .create_with_chunks(
                        ingestion_job_id=(
                            task.ingestion_job_id
                        ),
                        document_id=task.document_id,
                        chunks=chunks,
                    )
                )

            else:
                batch = existing_batch

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

            await self.uow.commit()

            if signals.dispatch_embedding:
                await (
                    self.downstream_task_scheduler
                    .dispatch_embedding(
                        task.ingestion_job_id,
                    )
                )

            if signals.dispatch_classification:
                await (
                    self.downstream_task_scheduler
                    .dispatch_classification(
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

    @staticmethod
    async def _read_json(
        content,
    ) -> dict:

        chunks: list[bytes] = []

        async for chunk in content:
            chunks.append(
                chunk,
            )

        return json.loads(
            b"".join(
                chunks
            ).decode(
                "utf-8"
            )
        )

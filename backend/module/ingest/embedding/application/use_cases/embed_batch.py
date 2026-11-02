import logging
import math
from datetime import datetime
from datetime import timezone
from datetime import timedelta
from uuid import UUID

from module.ingest.embedding.domain.contracts.batch_finalizer import (
    BatchFinalizer,
)
from module.ingest.embedding.domain.contracts.chunk_reader import (
    ChunkReader,
)
from module.ingest.embedding.domain.contracts.document_chunk_embedding_repository import (
    DocumentChunkEmbeddingRepository,
)
from module.ingest.embedding.domain.contracts.embedding_engine_resolver import (
    EmbeddingEngineResolver,
)
from module.ingest.embedding.domain.contracts.embedding_task_repository import (
    EmbeddingLeaseLostError,
    EmbeddingTaskRepository,
)
from module.ingest.embedding.domain.contracts.unit_of_work import (
    UnitOfWork,
)
from module.ingest.embedding.domain.entities.document_chunk_embedding import (
    DocumentChunkEmbedding,
)
from module.ingest.embedding.domain.enums.task_status import (
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


class EmbedBatchUseCase:

    def __init__(
        self,
        *,
        task_repository: EmbeddingTaskRepository,
        chunk_reader: ChunkReader,
        embedding_engine_resolver: EmbeddingEngineResolver,
        embedding_repository: DocumentChunkEmbeddingRepository,
        batch_finalizer: BatchFinalizer,
        uow: UnitOfWork,
        orchestration_progress_service: (
            OrchestrationProgressService
            | NoOpOrchestrationProgressService
            | None
        ) = None,
        max_attempts: int = 3,
        page_size: int = 32,
    ):
        self.task_repository = task_repository
        self.chunk_reader = chunk_reader
        self.embedding_engine_resolver = (
            embedding_engine_resolver
        )
        self.embedding_repository = embedding_repository
        self.batch_finalizer = batch_finalizer
        self.orchestration_progress_service = (
            orchestration_progress_service
            or NoOpOrchestrationProgressService()
        )
        self.uow = uow
        self.max_attempts = max_attempts
        if not 1 <= page_size <= 1000:
            raise ValueError('Embedding page size must be between 1 and 1000')
        self.page_size = page_size

    async def execute(
        self,
        task_id: UUID,
    ) -> None:

        task = await self.task_repository.get_by_id(
            task_id,
        )

        if task is None:
            raise ValueError(
                "Embedding task not found"
            )

        if task.status != TaskStatus.PROCESSING:
            raise ValueError(
                "Embedding task must be PROCESSING"
            )

        original_owner = task.claimed_by
        try:
            logger.info(
                "embedding usecase_start task_id=%s job_id=%s batch_id=%s",
                task_id,
                task.ingestion_job_id,
                task.batch_id,
            )

            embedding_engine = await self.embedding_engine_resolver.resolve_for_job(task.ingestion_job_id)
            processed = 0
            async for chunks in self.chunk_reader.iter_by_batch_id(task.batch_id, page_size=self.page_size):
                await self._embed_page(embedding_engine, chunks)
                processed += len(chunks)
            if not processed:
                raise ValueError('Cannot embed an empty chunk batch')
            logger.info('embedding chunks_processed task_id=%s chunks=%s', task_id, processed)

            signal = (
                await self.batch_finalizer
                .complete_embedding(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    batch_id=task.batch_id,
                )
            )

            if original_owner is not None:
                owned = await self.task_repository.renew_lease(
                    task_id, claimed_by=original_owner,
                    lease_until=datetime.now(timezone.utc) + timedelta(seconds=300),
                )
                if not owned:
                    raise EmbeddingLeaseLostError('Cannot complete embedding after losing its lease')
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
                    stage=IngestionStage.EMBEDDING,
                )
            )

            logger.info(
                "embedding commit task_id=%s",
                task_id,
            )
            await self.uow.commit()

            if signal.dispatch_index:
                logger.info(
                    "embedding dispatch_index job_id=%s",
                    task.ingestion_job_id,
                )
                await self.batch_finalizer.dispatch_index(
                    task.ingestion_job_id,
                )

        except EmbeddingLeaseLostError:
            await self.uow.rollback()
            raise
        except Exception as exc:
            logger.exception(
                "embedding failed task_id=%s error=%s",
                task_id,
                exc,
            )
            await self.uow.rollback()

            task = await self.task_repository.get_by_id(
                task_id,
            )

            if task is not None:
                if task.status != TaskStatus.PROCESSING or task.claimed_by != original_owner:
                    raise
                if original_owner is not None and not await self.task_repository.renew_lease(
                    task_id, claimed_by=original_owner,
                    lease_until=datetime.now(timezone.utc) + timedelta(seconds=300),
                ):
                    await self.uow.rollback()
                    raise
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
                            stage=IngestionStage.EMBEDDING,
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
                            stage=IngestionStage.EMBEDDING,
                        )
                    )

                await self.uow.commit()

                logger.info(
                    "embedding retry_state task_id=%s status=%s",
                    task_id,
                    task.status.value,
                )

            raise

    async def _embed_page(self, engine, chunks):
        if not chunks or any(not chunk.content.strip() for chunk in chunks):
            raise ValueError('Embedding page must contain readable chunks')
        expected = {chunk.id for chunk in chunks}
        results = await engine.embed_batch(chunks)
        actual = [result.chunk_id for result in results]
        if len(expected) != len(chunks) or len(actual) != len(expected) or set(actual) != expected:
            raise ValueError('Embedding must return exactly one result for every input chunk')
        if any(result.status != 'success' or not result.vector or type(result.dimension) is not int
               or result.dimension != len(result.vector)
               or any(type(value) not in (int, float) or not math.isfinite(value) for value in result.vector)
               for result in results):
            raise ValueError('Embedding engine returned an invalid or missing vector')
        await self.embedding_repository.upsert_many([
            DocumentChunkEmbedding(
                id=None, chunk_id=result.chunk_id, model_name=result.model_name,
                embedding=result.vector, dimension=result.dimension, token_count=result.token_count,
                created_at=None,
            ) for result in results
        ])

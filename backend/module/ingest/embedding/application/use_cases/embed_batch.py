from datetime import datetime
from datetime import timezone
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
        max_attempts: int = 3,
    ):
        self.task_repository = task_repository
        self.chunk_reader = chunk_reader
        self.embedding_engine_resolver = (
            embedding_engine_resolver
        )
        self.embedding_repository = embedding_repository
        self.batch_finalizer = batch_finalizer
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
                "Embedding task not found"
            )

        if task.status != TaskStatus.PROCESSING:
            raise ValueError(
                "Embedding task must be PROCESSING"
            )

        try:
            chunks = await self.chunk_reader.list_by_batch_id(
                task.batch_id,
            )

            embedding_engine = (
                await self.embedding_engine_resolver
                .resolve_for_job(
                    task.ingestion_job_id,
                )
            )

            results = await embedding_engine.embed_batch(
                chunks,
            )

            failed_results = [
                result
                for result in results
                if result.status == "error"
            ]

            if failed_results:
                raise RuntimeError(
                    "Embedding engine failed for "
                    f"{len(failed_results)} chunks"
                )

            embeddings = [
                DocumentChunkEmbedding(
                    id=None,
                    chunk_id=result.chunk_id,
                    model_name=result.model_name,
                    embedding=result.vector,
                    dimension=result.dimension,
                    token_count=result.token_count,
                    created_at=None,
                )
                for result in results
                if (
                    result.vector is not None
                    and result.dimension is not None
                )
            ]

            await self.embedding_repository.upsert_many(
                embeddings,
            )

            signal = (
                await self.batch_finalizer
                .complete_embedding(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    batch_id=task.batch_id,
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

            if signal.dispatch_index:
                await self.batch_finalizer.dispatch_index(
                    task.ingestion_job_id,
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

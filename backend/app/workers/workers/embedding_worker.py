from uuid import UUID

from app.application.embedding.engine import (
    EmbeddingEngine,
)

from app.application.embedding.schemas import (
    Chunk,
)

from app.domain.entities.document_chunk_embedding import (
    DocumentChunkEmbedding,
)

from app.domain.repositories.chunk_batch_repository import (
    ChunkBatchRepository,
)

from app.domain.repositories.document_chunk_embedding_repository import (
    DocumentChunkEmbeddingRepository,
)

from app.domain.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)

from app.domain.repositories.document_processing_task_repository import (
    DocumentProcessingTaskRepository,
)
from datetime import datetime, timezone


class EmbeddingWorker:

    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
    ) -> None:

        self._embedding_engine = (
            embedding_engine
        )

    async def execute(
        self,
        payload: dict,
        task_repository: DocumentProcessingTaskRepository,
        chunk_repository: DocumentChunkRepository,
        embedding_repository: DocumentChunkEmbeddingRepository,
        chunk_batch_repository: ChunkBatchRepository,
    ) -> None:

        task_id = UUID(
            payload["task_id"],
        )

        task = await task_repository.get_by_id(
            task_id,
        )

        if task is None:
            raise ValueError(
                f"Task {task_id} not found."
            )

        await task_repository.mark_running(
            task.id,
        )

        chunks = await (
            chunk_repository.list_by_batch_id(
                task.batch_id,
            )
        )

        engine_chunks = [
            Chunk(
                id=chunk.id,
                content=chunk.content,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]

        results = (
            self._embedding_engine.embed_batch(
                engine_chunks,
            )
        )

        entities = [
            DocumentChunkEmbedding(
                id=None,
                chunk_id=result.chunk_id,
                model_name=result.model_name,
                embedding=result.vector,
                dimension=result.dimension,
                token_count=result.token_count,
                created_at=datetime.now(timezone.utc),
            )
            for result in results
            if result.status == "ok"
        ]

        if entities:

            await embedding_repository.create_many(
                entities,
            )

        await task_repository.mark_completed(
            task.id,
        )

        batch_id = task.batch_id

        await (
            chunk_batch_repository.mark_embedding_completed(
                batch_id,
            )
        )

        completed = await (
            chunk_batch_repository.try_complete_batch(
                batch_id,
            )
        )

        if completed:

            print(
                f"Batch completed: "
                f"{batch_id}"
            )
from uuid import UUID

from app.application.classification.engine import (
    ClassificationEngine,
)

from app.application.classification.schemas import (
    Chunk,
)

from app.domain.entities.document_chunk_classification import (
    DocumentChunkClassification,
)

from app.domain.repositories.chunk_batch_repository import (
    ChunkBatchRepository,
)

from app.domain.repositories.document_chunk_classification_repository import (
    DocumentChunkClassificationRepository,
)

from app.domain.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)

from app.domain.repositories.document_processing_task_repository import (
    DocumentProcessingTaskRepository,
)
from datetime import datetime, timezone


class ClassificationWorker:

    def __init__(
        self,
        classification_engine: ClassificationEngine,
    ) -> None:

        self._classification_engine = (
            classification_engine
        )

    async def execute(
        self,
        payload: dict,
        task_repository: DocumentProcessingTaskRepository,
        chunk_batch_repository: ChunkBatchRepository,
        chunk_repository: DocumentChunkRepository,
        classification_repository: DocumentChunkClassificationRepository,
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

        results = await (
            self._classification_engine.classify_batch(
                engine_chunks,
            )
        )

        entities = [
            DocumentChunkClassification(
                id=None,
                model_name=result.model_name,
                chunk_id=result.chunk_id,
                label=result.label,
                confidence=result.confidence,
                raw_response=result.raw_response,
                created_at=datetime.now(timezone.utc),
            )
            for result in results
           
        ]


        if entities:

            await classification_repository.create_many(
                entities,
            )

        await task_repository.mark_completed(
            task.id,
        )

        batch_id = task.batch_id

        await (
            chunk_batch_repository.mark_classification_completed(
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
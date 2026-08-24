from datetime import datetime
from datetime import timezone

from app.application.chunking.chunking_engine import (
    ChunkingEngine,
)

from app.application.ingestion.messages.chunk_message import (
    ChunkMessage,
)

from app.domain.entities.document_processing_task import (
    DocumentProcessingTask,
)

from app.domain.enums.task_status import (
    TaskStatus,
)

from app.domain.enums.task_type import (
    TaskType,
)

from app.domain.repositories.chunk_batch_repository import (
    ChunkBatchRepository,
)

from app.domain.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)

from app.domain.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)

from app.domain.repositories.document_processing_task_repository import (
    DocumentProcessingTaskRepository,
)

from app.domain.services.chunk_batch_builder import (
    ChunkBatchBuilder,
)

from app.domain.ports.storage.chunk.chunk_storage import (
    ChunkStorage,
)


class ChunkWorker:

    def __init__(
        self,
        chunking_engine: ChunkingEngine,
        chunk_batch_builder: ChunkBatchBuilder,
        chunk_storage: ChunkStorage,
        embedding_dispatcher,
        classification_dispatcher,
    ) -> None:

        self.chunking_engine = (
            chunking_engine
        )

        self.chunk_batch_builder = (
            chunk_batch_builder
        )

        self.chunk_storage = (
            chunk_storage
        )

        self.embedding_dispatcher = (
            embedding_dispatcher
        )

        self.classification_dispatcher = (
            classification_dispatcher
        )

    async def execute(
        self,
        message: ChunkMessage,
        extraction_repository: DocumentExtractionRepository,
        chunk_batch_repository: ChunkBatchRepository,
        document_chunk_repository: DocumentChunkRepository,
        task_repository: DocumentProcessingTaskRepository,
    ) -> list[tuple[str, str]]:

        extraction = await (
            extraction_repository.get_by_id(
                message.extraction_id,
            )
        )

        print("=" * 80)
        print("CHUNK WORKER START")
        print(
            f"Document   : "
            f"{message.document_id}"
        )
        print(
            f"Extraction : "
            f"{message.extraction_id}"
        )
        print(
            f"Extraction Found : "
            f"{extraction is not None}"
        )

        if extraction is None:
            raise ValueError(
                f"Extraction "
                f"{message.extraction_id} "
                f"not found."
            )

        chunks = list(
            self.chunking_engine.chunk(
                extraction,
            )
        )

        print(
            f"Chunking completed -> "
            f"{len(chunks)} chunks"
        )

        result = (
            self.chunk_batch_builder.build(
                document_id=message.document_id,
                chunks=chunks,
            )
        )

        print(
            f"Build result -> "
            f"batches={len(result.batches)}, "
            f"chunks={len(result.chunks)}"
        )

        print("Saving ChunkBatch...")

        for batch in result.batches:

            await chunk_batch_repository.create(
                batch,
            )

        print(
            f"Saving "
            f"{len(result.chunks)} "
            f"document chunks..."
        )

        await document_chunk_repository.create_many(
            result.chunks,
        )

        for batch in result.batches:

            batch_chunks = [
                chunk
                for chunk in result.chunks
                if chunk.batch_id == batch.id
            ]

            await self.chunk_storage.save(
                document_id=message.document_id,
                batch_id=batch.id,
                chunks=batch_chunks,
            )

            print(
                f"Storage saved "
                f"batch={batch.batch_index}"
            )

        # --------------------------------------------------
        # Create processing tasks
        # --------------------------------------------------

        pending_tasks: list[tuple[str, str]] = []

        for batch in result.batches:

            now = datetime.now(
                timezone.utc,
            )

            embedding_task = (
                DocumentProcessingTask(
                    id=None,
                    document_id=message.document_id,
                    batch_id=batch.id,
                    task_type=TaskType.EMBED,
                    status=TaskStatus.PENDING,
                    retry_count=0,
                    error_message=None,
                    started_at=None,
                    finished_at=None,
                    created_at=now,
                    updated_at=now,
                )
            )

            classification_task = (
                DocumentProcessingTask(
                    id=None,
                    document_id=message.document_id,
                    batch_id=batch.id,
                    task_type=TaskType.CLASSIFY,
                    status=TaskStatus.PENDING,
                    retry_count=0,
                    error_message=None,
                    started_at=None,
                    finished_at=None,
                    created_at=now,
                    updated_at=now,
                )
            )

            embedding_task = await (
                task_repository.create(
                    embedding_task,
                )
            )

            classification_task = await (
                task_repository.create(
                    classification_task,
                )
            )

            print(
                f"Created EMBED task="
                f"{embedding_task.id} "
                f"batch={batch.id}"
            )

            print(
                f"Created CLASSIFY task="
                f"{classification_task.id} "
                f"batch={batch.id}"
            )

            pending_tasks.append(
                (
                    str(embedding_task.id),
                    str(classification_task.id),
                )
            )

        print(
            "Created all processing tasks."
        )

        print(
            "ChunkWorker finished. "
            "Queues will be published after DB commit."
        )

        # --------------------------------------------------
        # IMPORTANT:
        # DO NOT publish queue messages here.
        #
        # The ChunkConsumer must commit the transaction
        # first, then publish these task IDs.
        # --------------------------------------------------

        print("=" * 80)
        print("CHUNK PIPELINE")
        print("=" * 80)

        print(
            f"Document Id   : "
            f"{message.document_id}"
        )

        print(
            f"Extraction Id : "
            f"{message.extraction_id}"
        )

        print(
            f"Batch Count   : "
            f"{len(result.batches)}"
        )

        print(
            f"Chunk Count   : "
            f"{len(result.chunks)}"
        )

        print("=" * 80)

        for batch in result.batches:

            batch_chunks = [
                chunk
                for chunk in result.chunks
                if chunk.batch_id == batch.id
            ]

            print(
                f"Batch {batch.batch_index} "
                f"({len(batch_chunks)} chunks)"
            )

            for chunk in batch_chunks:

                print(
                    f"[{chunk.chunk_index}] "
                    f"{chunk.title}"
                )

                print(
                    f"Length : "
                    f"{len(chunk.content)}"
                )

                print(
                    chunk.content[:200]
                )

                print("-" * 80)

        return pending_tasks
import asyncio
import traceback

from app.infrastructure.persistence.connection import (
    AsyncSessionLocal,
)

from app.infrastructure.persistence.repositories.document_extraction_repository_impl import (
    DocumentExtractionRepositoryImpl,
)

from app.infrastructure.persistence.repositories.document_chunk_repository_impl import (
    DocumentChunkRepositoryImpl,
)

from app.infrastructure.persistence.repositories.chunk_batch_repository_impl import (
    ChunkBatchRepositoryImpl,
)

from app.infrastructure.persistence.repositories.document_processing_task_impl import (
    DocumentProcessingTaskRepositoryImpl,
)

from app.shared.queue.queue_manager import (
    queue_manager,
)


class ChunkConsumer:

    def __init__(
        self,
        chunk_worker,
    ) -> None:

        print("=" * 80)
        print("CHUNK CONSUMER STARTED")

        self.chunk_worker = chunk_worker

    async def start(
        self,
    ) -> None:

        queue = queue_manager.get_queue(
            "chunk",
        )

        while True:

            try:

                print("1")

                message = await queue.dequeue()

                print(
                    "2",
                    message,
                )

                async with AsyncSessionLocal() as session:

                    print("3")

                    extraction_repository = (
                        DocumentExtractionRepositoryImpl(
                            session,
                        )
                    )

                    chunk_batch_repository = (
                        ChunkBatchRepositoryImpl(
                            session,
                        )
                    )

                    document_chunk_repository = (
                        DocumentChunkRepositoryImpl(
                            session,
                        )
                    )

                    task_repository = (
                        DocumentProcessingTaskRepositoryImpl(
                            session,
                        )
                    )

                    print("4")

                    pending_tasks = (
                        await self.chunk_worker.execute(
                            message=message,
                            extraction_repository=extraction_repository,
                            chunk_batch_repository=chunk_batch_repository,
                            document_chunk_repository=document_chunk_repository,
                            task_repository=task_repository,
                        )
                    )

                    print(
                        f"Created "
                        f"{len(pending_tasks)} "
                        f"EMBED/CLASSIFY task pairs"
                    )

                    # --------------------------------------------------
                    # IMPORTANT:
                    # Commit DB BEFORE publishing queue messages.
                    # --------------------------------------------------

                    await session.commit()

                    print("5 - DB COMMITTED")

                # ------------------------------------------------------
                # Publish AFTER the database transaction is committed.
                # ------------------------------------------------------

                for (
                    embedding_task_id,
                    classification_task_id,
                ) in pending_tasks:

                    print(
                        "Publishing tasks:",
                        embedding_task_id,
                        classification_task_id,
                    )

                    await asyncio.gather(
                        self.chunk_worker.embedding_dispatcher.dispatch(
                            embedding_task_id,
                        ),
                        self.chunk_worker.classification_dispatcher.dispatch(
                            classification_task_id,
                        ),
                    )

                    print(
                        "Published tasks:",
                        embedding_task_id,
                        classification_task_id,
                    )

                print("6 - CHUNK MESSAGE FINISHED")

            except Exception:

                print("=" * 80)
                print("CHUNK CONSUMER ERROR")

                traceback.print_exc()

                print("=" * 80)
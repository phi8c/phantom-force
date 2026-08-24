import json

from azure.servicebus.aio import (
    ServiceBusClient,
)

from app.infrastructure.persistence.connection import (
    AsyncSessionLocal,
)

from app.infrastructure.persistence.repositories.document_chunk_classification_impl import (
    DocumentChunkClassificationRepositoryImpl,
)

from app.infrastructure.persistence.repositories.document_chunk_repository_impl import (
    DocumentChunkRepositoryImpl,
)

from app.infrastructure.persistence.repositories.document_processing_task_impl import (
    DocumentProcessingTaskRepositoryImpl,
)

from app.infrastructure.persistence.repositories.chunk_batch_repository_impl import (
    ChunkBatchRepositoryImpl,
)

from app.shared.config.settings import (
    settings,
)

from app.workers.workers.classification_worker import (
    ClassificationWorker,
)


class ClassificationConsumer:

    def __init__(
        self,
        classification_worker: ClassificationWorker,
    ) -> None:

        self._classification_worker = (
            classification_worker
        )

        self._connection_string = (
            settings.AZURE_SERVICE_BUS_CONNECTION_STRING
        )

        self._queue_name = (
            settings.AZURE_SERVICE_BUS_CLASSIFY_QUEUE
        )

    async def start(
        self,
    ) -> None:

        client = (
            ServiceBusClient.from_connection_string(
                self._connection_string,
            )
        )

        async with client:

            receiver = (
                client.get_queue_receiver(
                    queue_name=self._queue_name,
                    max_wait_time=5,
                )
            )

            async with receiver:

                while True:

                    messages = await (
                        receiver.receive_messages(
                            max_message_count=10,
                        )
                    )   

                    for message in messages:

                        payload = json.loads(
                            str(message),
                        )

                        async with AsyncSessionLocal() as session:

                            task_repository = (
                                DocumentProcessingTaskRepositoryImpl(
                                    session,
                                )
                            )

                            chunk_repository = (
                                DocumentChunkRepositoryImpl(
                                    session,
                                )
                            )

                            classification_repository = (
                                DocumentChunkClassificationRepositoryImpl(
                                    session,
                                )
                            )

                            chunk_batch_repository = (
                                ChunkBatchRepositoryImpl(
                                    session,
                                )
                            )

                            await (
                                self._classification_worker.execute(
                                    payload=payload,
                                    task_repository=task_repository,
                                    chunk_repository=chunk_repository,
                                    classification_repository=(
                                        classification_repository
                                    ),
                                    chunk_batch_repository=(
                                        chunk_batch_repository
                                    ),
                                )
                            )

                            await session.commit()

                        await receiver.complete_message(
                            message,
                        )
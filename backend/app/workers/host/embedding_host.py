from app.workers.consumers.embedding_consumer import (
    EmbeddingConsumer,
)

from app.workers.workers.embedding_worker import (
    EmbeddingWorker,
)


class EmbeddingHost:

    def __init__(
        self,
        embedding_worker: EmbeddingWorker,
    ) -> None:

        self._consumer = (
            EmbeddingConsumer(
                embedding_worker=embedding_worker,
            )
        )

    async def start(
        self,
    ) -> None:

        await self._consumer.start()
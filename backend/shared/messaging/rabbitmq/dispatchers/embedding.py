from __future__ import annotations

from uuid import UUID

from module.ingest.embedding.domain.contracts.embedding_dispatcher import (
    EmbeddingDispatcher,
)

from ..publisher import RabbitMQPublisher


class RabbitMQEmbeddingDispatcher(EmbeddingDispatcher):
    def __init__(self, publisher: RabbitMQPublisher, queue_name: str) -> None:
        self._publisher = publisher
        self._queue_name = queue_name

    async def dispatch_job(self, ingestion_job_id: UUID) -> None:
        await self._publisher.publish(
            self._queue_name,
            {"ingestion_job_id": str(ingestion_job_id)},
        )

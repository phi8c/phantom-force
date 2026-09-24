from __future__ import annotations

from uuid import UUID

from module.ingest.discovery.domain.contracts.discovery_dispatcher import (
    DiscoveryDispatcher,
)

from ..publisher import RabbitMQPublisher


class RabbitMQDiscoveryDispatcher(DiscoveryDispatcher):
    def __init__(self, publisher: RabbitMQPublisher, queue_name: str) -> None:
        self._publisher = publisher
        self._queue_name = queue_name

    async def dispatch(
        self,
        ingestion_job_id: UUID,
        batch_size: int,
    ) -> None:
        await self._publisher.publish(
            self._queue_name,
            {
                "ingestion_job_id": str(ingestion_job_id),
                "batch_size": batch_size,
            },
        )

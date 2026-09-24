from __future__ import annotations

from uuid import UUID

from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.knowledge_space.domain.contracts.queue_provider_resolver import (
    QueueProviderResolver,
)
from shared.messaging.contracts.queue_routing_resolver import (
    QueueRoutingResolver,
)


class IngestionJobQueueRoutingResolver(QueueRoutingResolver):
    def __init__(
        self,
        ingestion_repository: IngestionConfigRepository,
        queue_provider_resolver: QueueProviderResolver,
    ) -> None:
        self._ingestion_repository = ingestion_repository
        self._queue_provider_resolver = queue_provider_resolver

    async def resolve_for_job(self, ingestion_job_id: UUID) -> str:
        job = await self._ingestion_repository.get_job_by_id(
            ingestion_job_id
        )
        if job is None:
            raise LookupError(
                f"Ingestion job '{ingestion_job_id}' was not found."
            )
        return await self._queue_provider_resolver.resolve(
            job.knowledge_space_id
        )

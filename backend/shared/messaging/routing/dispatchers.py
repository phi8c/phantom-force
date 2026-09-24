from __future__ import annotations

from uuid import UUID

from module.ingest.chunking.domain.contracts.chunking_dispatcher import (
    ChunkingDispatcher,
)
from module.ingest.classification.domain.contracts.classification_dispatcher import (
    ClassificationDispatcher,
)
from module.ingest.config.domain.contracts.discovery_dispatcher import (
    DiscoveryDispatcher as ConfigDiscoveryDispatcher,
)
from module.ingest.discovery.domain.contracts.discovery_dispatcher import (
    DiscoveryDispatcher,
)
from module.ingest.download.domain.contracts.download_dispatcher import (
    DownloadDispatcher,
)
from module.ingest.embedding.domain.contracts.embedding_dispatcher import (
    EmbeddingDispatcher,
)
from module.ingest.extraction.domain.contracts.extraction_dispatcher import (
    ExtractionDispatcher,
)
from shared.messaging.composition.models import IngestDispatchers
from shared.messaging.composition.provider_registry import (
    MessagingProviderRegistry,
)
from shared.messaging.contracts.queue_routing_resolver import (
    QueueRoutingResolver,
)


class _RoutingDispatcher:
    def __init__(
        self,
        resolver: QueueRoutingResolver,
        registry: MessagingProviderRegistry,
    ) -> None:
        self._resolver = resolver
        self._registry = registry

    async def _provider_dispatchers(
        self,
        ingestion_job_id: UUID,
    ) -> IngestDispatchers:
        provider_code = await self._resolver.resolve_for_job(
            ingestion_job_id
        )
        return self._registry.get(provider_code)


class RoutingDiscoveryDispatcher(
    _RoutingDispatcher,
    ConfigDiscoveryDispatcher,
    DiscoveryDispatcher,
):
    async def dispatch(
        self,
        ingestion_job_id: UUID,
        batch_size: int,
    ) -> None:
        dispatchers = await self._provider_dispatchers(ingestion_job_id)
        await dispatchers.discovery.dispatch(
            ingestion_job_id,
            batch_size,
        )


class RoutingDownloadDispatcher(_RoutingDispatcher, DownloadDispatcher):
    async def dispatch(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(ingestion_job_id)
        await dispatchers.download.dispatch(ingestion_job_id)


class RoutingExtractionDispatcher(
    _RoutingDispatcher,
    ExtractionDispatcher,
):
    async def dispatch(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(ingestion_job_id)
        await dispatchers.extraction.dispatch(ingestion_job_id)


class RoutingChunkingDispatcher(_RoutingDispatcher, ChunkingDispatcher):
    async def dispatch(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(ingestion_job_id)
        await dispatchers.chunking.dispatch(ingestion_job_id)


class RoutingEmbeddingDispatcher(_RoutingDispatcher, EmbeddingDispatcher):
    async def dispatch_job(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(ingestion_job_id)
        await dispatchers.embedding.dispatch_job(ingestion_job_id)


class RoutingClassificationDispatcher(
    _RoutingDispatcher,
    ClassificationDispatcher,
):
    async def dispatch_job(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(ingestion_job_id)
        await dispatchers.classification.dispatch_job(ingestion_job_id)


def create_routing_dispatchers(
    resolver: QueueRoutingResolver,
    registry: MessagingProviderRegistry,
) -> IngestDispatchers:
    return IngestDispatchers(
        discovery=RoutingDiscoveryDispatcher(resolver, registry),
        download=RoutingDownloadDispatcher(resolver, registry),
        extraction=RoutingExtractionDispatcher(resolver, registry),
        chunking=RoutingChunkingDispatcher(resolver, registry),
        embedding=RoutingEmbeddingDispatcher(resolver, registry),
        classification=RoutingClassificationDispatcher(
            resolver,
            registry,
        ),
    )

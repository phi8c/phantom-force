from __future__ import annotations

import logging
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
    DispatcherProviderRegistry,
)
from shared.messaging.contracts.queue_routing_resolver import (
    QueueRoutingResolver,
)


logger = logging.getLogger(__name__)


class _RoutingDispatcher:
    def __init__(
        self,
        resolver: QueueRoutingResolver,
        registry: DispatcherProviderRegistry,
    ) -> None:
        self._resolver = resolver
        self._registry = registry

    async def _provider_dispatchers(
        self,
        ingestion_job_id: UUID,
        stage: str,
    ) -> IngestDispatchers:
        provider_code = await self._resolver.resolve_for_job(
            ingestion_job_id
        )
        logger.info(
            "ingest dispatch route_resolved job_id=%s stage=%s queue_provider=%s",
            ingestion_job_id,
            stage,
            provider_code,
        )
        return await self._registry.get(provider_code)


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
        dispatchers = await self._provider_dispatchers(
            ingestion_job_id,
            "discovery",
        )
        await dispatchers.discovery.dispatch(
            ingestion_job_id,
            batch_size,
        )


class RoutingDownloadDispatcher(_RoutingDispatcher, DownloadDispatcher):
    async def dispatch(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(
            ingestion_job_id,
            "download",
        )
        await dispatchers.download.dispatch(ingestion_job_id)


class RoutingExtractionDispatcher(
    _RoutingDispatcher,
    ExtractionDispatcher,
):
    async def dispatch(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(
            ingestion_job_id,
            "extraction",
        )
        await dispatchers.extraction.dispatch(ingestion_job_id)


class RoutingChunkingDispatcher(_RoutingDispatcher, ChunkingDispatcher):
    async def dispatch(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(
            ingestion_job_id,
            "chunking",
        )
        await dispatchers.chunking.dispatch(ingestion_job_id)


class RoutingEmbeddingDispatcher(_RoutingDispatcher, EmbeddingDispatcher):
    async def dispatch_job(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(
            ingestion_job_id,
            "embedding",
        )
        await dispatchers.embedding.dispatch_job(ingestion_job_id)


class RoutingClassificationDispatcher(
    _RoutingDispatcher,
    ClassificationDispatcher,
):
    async def dispatch_job(self, ingestion_job_id: UUID) -> None:
        dispatchers = await self._provider_dispatchers(
            ingestion_job_id,
            "classification",
        )
        await dispatchers.classification.dispatch_job(ingestion_job_id)


def create_routing_dispatchers(
    resolver: QueueRoutingResolver,
    registry: DispatcherProviderRegistry,
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

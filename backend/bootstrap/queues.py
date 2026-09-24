from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

from shared.messaging.composition import (
    MessagingProviderRegistry,
    MessagingResourceGroup,
    create_composite_consumers,
    IngestConsumers,
    IngestDispatchers,
    IngestMessaging,
    IngestProducer,
)
from shared.messaging.contracts import QueueRoutingResolver
from shared.messaging.routing import (
    ScopedQueueRoutingResolver,
    create_routing_dispatchers,
)


AZURE_SERVICE_BUS = "azure_service_bus"
RABBITMQ = "rabbitmq"


async def create_ingest_messaging() -> IngestMessaging:
    azure = await _create_azure_messaging()
    try:
        rabbitmq = await _create_rabbitmq_messaging()
    except Exception:
        await azure.close()
        raise

    resources = MessagingResourceGroup([azure.close, rabbitmq.close])
    try:
        provider_dispatchers = {
            AZURE_SERVICE_BUS: azure.dispatchers,
            RABBITMQ: rabbitmq.dispatchers,
        }
        consumers = create_composite_consumers(
            {
                AZURE_SERVICE_BUS: azure.consumers,
                RABBITMQ: rabbitmq.consumers,
            }
        )
        dispatchers = _create_provider_aware_dispatchers(
            provider_dispatchers
        )
    except Exception:
        await resources.close()
        raise

    return IngestMessaging(
        consumers=consumers,
        dispatchers=dispatchers,
        _close_callback=resources.close,
    )


async def create_ingest_producer() -> IngestProducer:
    azure = await _create_azure_producer()
    try:
        rabbitmq = await _create_rabbitmq_producer()
    except Exception:
        await azure.close()
        raise

    resources = MessagingResourceGroup([azure.close, rabbitmq.close])
    try:
        dispatchers = _create_provider_aware_dispatchers(
            {
                AZURE_SERVICE_BUS: azure.dispatchers,
                RABBITMQ: rabbitmq.dispatchers,
            }
        )
    except Exception:
        await resources.close()
        raise

    return IngestProducer(
        dispatchers=dispatchers,
        _close_callback=resources.close,
    )


def _create_provider_aware_dispatchers(
    provider_dispatchers: dict[str, IngestDispatchers],
) -> IngestDispatchers:
    resolver = ScopedQueueRoutingResolver(_queue_routing_resolver_scope)
    return create_routing_dispatchers(
        resolver,
        MessagingProviderRegistry(provider_dispatchers),
    )


@asynccontextmanager
async def _queue_routing_resolver_scope(
) -> AsyncIterator[QueueRoutingResolver]:
    from bootstrap.database import async_session_factory
    from module.ingest.config.application.services.queue_routing_resolver import (
        IngestionJobQueueRoutingResolver,
    )
    from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import (
        IngestionConfigRepositoryImpl,
    )
    from module.knowledge_space.application.services.queue_provider_resolver import (
        KnowledgeSpaceQueueProviderResolver,
    )
    from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_queue_repository_impl import (
        KnowledgeSpaceQueueRepositoryImpl,
    )
    from shared.config.settings import settings

    async with async_session_factory() as session:
        yield IngestionJobQueueRoutingResolver(
            ingestion_repository=IngestionConfigRepositoryImpl(
                session
            ),
            queue_provider_resolver=(
                KnowledgeSpaceQueueProviderResolver(
                    KnowledgeSpaceQueueRepositoryImpl(session),
                    fallback_provider_code=settings.QUEUE_PROVIDER,
                )
            ),
        )


async def _create_azure_messaging() -> IngestMessaging:
    from shared.messaging.azure_service_bus.composition import (
        close_ingest_queue_clients,
        create_ingest_dispatchers,
        create_ingest_queue_clients,
    )

    clients = create_ingest_queue_clients()
    try:
        dispatchers = create_ingest_dispatchers(clients)
    except Exception:
        await close_ingest_queue_clients(clients)
        raise

    consumers = IngestConsumers(
        discovery=clients.discovery,
        download=clients.download,
        extraction=clients.extraction,
        chunking=clients.chunking,
        embedding=clients.embedding,
        classification=clients.classification,
    )
    return IngestMessaging(
        consumers=consumers,
        dispatchers=dispatchers,
        _close_callback=partial(
            close_ingest_queue_clients,
            clients,
        ),
    )


async def _create_rabbitmq_messaging() -> IngestMessaging:
    from shared.messaging.rabbitmq.composition import (
        create_rabbitmq_consumers,
        create_rabbitmq_dispatchers,
    )

    resources = await create_rabbitmq_consumers()
    try:
        dispatchers = await create_rabbitmq_dispatchers(resources)
    except Exception:
        await resources.close()
        raise

    return IngestMessaging(
        consumers=resources.consumers,
        dispatchers=dispatchers,
        _close_callback=resources.close,
    )


async def _create_azure_producer() -> IngestProducer:
    from shared.messaging.azure_service_bus.composition import (
        create_azure_producer,
    )

    resources = await create_azure_producer()
    return IngestProducer(
        dispatchers=resources.dispatchers,
        _close_callback=resources.close,
    )


async def _create_rabbitmq_producer() -> IngestProducer:
    from shared.messaging.rabbitmq.composition import (
        create_rabbitmq_producer,
    )

    resources = await create_rabbitmq_producer()
    return IngestProducer(
        dispatchers=resources.dispatchers,
        _close_callback=resources.close,
    )


__all__ = [
    "IngestConsumers",
    "IngestDispatchers",
    "IngestMessaging",
    "IngestProducer",
    "create_ingest_messaging",
    "create_ingest_producer",
]

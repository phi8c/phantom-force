from __future__ import annotations

from functools import partial

from shared.messaging.composition import (
    IngestConsumers,
    IngestDispatchers,
    IngestMessaging,
)


AZURE_SERVICE_BUS = "azure_service_bus"
RABBITMQ = "rabbitmq"


async def create_ingest_messaging(
    provider: str | None = None,
) -> IngestMessaging:
    selected_provider = provider or _configured_provider()
    normalized_provider = selected_provider.strip().lower()

    if normalized_provider == AZURE_SERVICE_BUS:
        return await _create_azure_messaging()
    if normalized_provider == RABBITMQ:
        return await _create_rabbitmq_messaging()
    raise RuntimeError(
        "Unsupported QUEUE_PROVIDER "
        f"'{selected_provider}'. Expected '{AZURE_SERVICE_BUS}' or '{RABBITMQ}'."
    )


def _configured_provider() -> str:
    from shared.config.settings import settings

    return settings.QUEUE_PROVIDER


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


__all__ = [
    "IngestConsumers",
    "IngestDispatchers",
    "IngestMessaging",
    "create_ingest_messaging",
]

from dataclasses import dataclass
from typing import Any

from shared.messaging.composition import IngestDispatchers
from shared.messaging.azure_service_bus.consumer import AzureMessageConsumer
from shared.messaging.azure_service_bus.dispatchers import (
    AzureChunkingDispatcher,
    AzureClassificationDispatcher,
    AzureDiscoveryDispatcher,
    AzureDownloadDispatcher,
    AzureEmbeddingDispatcher,
    AzureExtractionDispatcher,
)


def _settings() -> Any:
    from shared.config.settings import settings

    return settings


@dataclass(frozen=True)
class IngestQueueClients:
    service_bus_client: object
    discovery: object
    download: object
    extraction: object
    chunking: object
    embedding: object
    classification: object


@dataclass(frozen=True)
class AzureProducerResources:
    dispatchers: IngestDispatchers
    service_bus_client: object

    async def close(self) -> None:
        await self.service_bus_client.close()


def create_service_bus_client():
    configuration = _settings()

    if not configuration.AZURE_SERVICE_BUS_CONNECTION_STRING:
        raise RuntimeError(
            "AZURE_SERVICE_BUS_CONNECTION_STRING is required"
        )

    from azure.servicebus.aio import ServiceBusClient

    return ServiceBusClient.from_connection_string(
        conn_str=configuration.AZURE_SERVICE_BUS_CONNECTION_STRING,
    )


def create_ingest_queue_clients() -> IngestQueueClients:

    configuration = _settings()
    service_bus_client = create_service_bus_client()
    discovery_queue_name = (
        configuration.AZURE_SERVICE_BUS_QUEUE_NAME
        or configuration.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE
    )

    return IngestQueueClients(
        service_bus_client=service_bus_client,
        discovery=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=discovery_queue_name,
            ),
        ),
        download=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=configuration.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE,
            ),
        ),
        extraction=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=configuration.AZURE_SERVICE_BUS_EXTRACT_QUEUE,
            ),
        ),
        chunking=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=configuration.AZURE_SERVICE_BUS_CHUNK_QUEUE,
            ),
        ),
        embedding=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=configuration.AZURE_SERVICE_BUS_EMBED_QUEUE,
            ),
        ),
        classification=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=configuration.AZURE_SERVICE_BUS_CLASSIFY_QUEUE,
            ),
        ),
    )


def create_ingest_dispatchers(
    clients: IngestQueueClients,
) -> IngestDispatchers:
    return _create_ingest_dispatchers(
        clients.service_bus_client,
        _settings(),
    )


def _create_ingest_dispatchers(
    service_bus_client: object,
    configuration: Any,
) -> IngestDispatchers:

    return IngestDispatchers(
        discovery=AzureDiscoveryDispatcher(
            service_bus_client=service_bus_client,
            queue_name=(
                configuration.AZURE_SERVICE_BUS_QUEUE_NAME
                or configuration.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE
            ),
        ),
        download=AzureDownloadDispatcher(
            service_bus_client=service_bus_client,
            queue_name=(
                configuration.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE
            ),
        ),
        extraction=AzureExtractionDispatcher(
            service_bus_client=service_bus_client,
            queue_name=(
                configuration.AZURE_SERVICE_BUS_EXTRACT_QUEUE
            ),
        ),
        chunking=AzureChunkingDispatcher(
            service_bus_client=service_bus_client,
            queue_name=(
                configuration.AZURE_SERVICE_BUS_CHUNK_QUEUE
            ),
        ),
        embedding=AzureEmbeddingDispatcher(
            service_bus_client=service_bus_client,
            queue_name=(
                configuration.AZURE_SERVICE_BUS_EMBED_QUEUE
            ),
        ),
        classification=AzureClassificationDispatcher(
            service_bus_client=service_bus_client,
            queue_name=(
                configuration.AZURE_SERVICE_BUS_CLASSIFY_QUEUE
            ),
        ),
    )


async def create_azure_producer() -> AzureProducerResources:
    client = create_service_bus_client()
    try:
        dispatchers = _create_ingest_dispatchers(client, _settings())
    except Exception:
        await client.close()
        raise
    return AzureProducerResources(dispatchers, client)


async def close_ingest_queue_clients(
    clients: IngestQueueClients,
) -> None:

    for resource in (
        clients.discovery,
        clients.download,
        clients.extraction,
        clients.chunking,
        clients.embedding,
        clients.classification,
        clients.service_bus_client,
    ):
        close = getattr(
            resource,
            "close",
            None,
        )

        if close is not None:
            await close()

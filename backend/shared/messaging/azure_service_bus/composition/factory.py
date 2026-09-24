from dataclasses import dataclass

from shared.config.settings import settings
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


@dataclass(frozen=True)
class IngestQueueClients:
    service_bus_client: object
    discovery: object
    download: object
    extraction: object
    chunking: object
    embedding: object
    classification: object


def create_service_bus_client():

    if not settings.AZURE_SERVICE_BUS_CONNECTION_STRING:
        raise RuntimeError(
            "AZURE_SERVICE_BUS_CONNECTION_STRING is required"
        )

    from azure.servicebus.aio import ServiceBusClient

    return ServiceBusClient.from_connection_string(
        conn_str=settings.AZURE_SERVICE_BUS_CONNECTION_STRING,
    )


def create_ingest_queue_clients() -> IngestQueueClients:

    service_bus_client = create_service_bus_client()
    discovery_queue_name = (
        settings.AZURE_SERVICE_BUS_QUEUE_NAME
        or settings.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE
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
                queue_name=settings.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE,
            ),
        ),
        extraction=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=settings.AZURE_SERVICE_BUS_EXTRACT_QUEUE,
            ),
        ),
        chunking=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=settings.AZURE_SERVICE_BUS_CHUNK_QUEUE,
            ),
        ),
        embedding=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=settings.AZURE_SERVICE_BUS_EMBED_QUEUE,
            ),
        ),
        classification=AzureMessageConsumer(
            service_bus_client.get_queue_receiver(
                queue_name=settings.AZURE_SERVICE_BUS_CLASSIFY_QUEUE,
            ),
        ),
    )


def create_ingest_dispatchers(
    clients: IngestQueueClients,
) -> IngestDispatchers:

    return IngestDispatchers(
        discovery=AzureDiscoveryDispatcher(
            service_bus_client=clients.service_bus_client,
            queue_name=(
                settings.AZURE_SERVICE_BUS_QUEUE_NAME
                or settings.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE
            ),
        ),
        download=AzureDownloadDispatcher(
            service_bus_client=clients.service_bus_client,
            queue_name=(
                settings.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE
            ),
        ),
        extraction=AzureExtractionDispatcher(
            service_bus_client=clients.service_bus_client,
            queue_name=(
                settings.AZURE_SERVICE_BUS_EXTRACT_QUEUE
            ),
        ),
        chunking=AzureChunkingDispatcher(
            service_bus_client=clients.service_bus_client,
            queue_name=(
                settings.AZURE_SERVICE_BUS_CHUNK_QUEUE
            ),
        ),
        embedding=AzureEmbeddingDispatcher(
            service_bus_client=clients.service_bus_client,
            queue_name=(
                settings.AZURE_SERVICE_BUS_EMBED_QUEUE
            ),
        ),
        classification=AzureClassificationDispatcher(
            service_bus_client=clients.service_bus_client,
            queue_name=(
                settings.AZURE_SERVICE_BUS_CLASSIFY_QUEUE
            ),
        ),
    )


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

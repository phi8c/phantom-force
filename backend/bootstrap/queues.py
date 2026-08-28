from dataclasses import dataclass

from shared.config.settings import settings

from module.ingest.chunking.infrastructure.messaging.azure_chunking_dispatcher import (
    AzureChunkingDispatcher,
)
from module.ingest.classification.infrastructure.messaging.azure_classification_dispatcher import (
    AzureClassificationDispatcher,
)
from module.ingest.discovery.infrastructure.messaging.azure.azure_discovery_dispatcher import (
    AzureDiscoveryDispatcher,
)
from module.ingest.download.infrastructure.messaging.azure_download_dispatcher import (
    AzureDownloadDispatcher,
)
from module.ingest.embedding.infrastructure.messaging.azure_embedding_dispatcher import (
    AzureEmbeddingDispatcher,
)
from module.ingest.extraction.infrastructure.messaging.azure_extraction_dispatcher import (
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
    discovery_sender: object
    download_sender: object
    extraction_sender: object
    chunking_sender: object
    embedding_sender: object
    classification_sender: object


@dataclass(frozen=True)
class IngestDispatchers:
    discovery: AzureDiscoveryDispatcher
    download: AzureDownloadDispatcher
    extraction: AzureExtractionDispatcher
    chunking: AzureChunkingDispatcher
    embedding: AzureEmbeddingDispatcher
    classification: AzureClassificationDispatcher


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
        discovery=service_bus_client.get_queue_receiver(
            queue_name=discovery_queue_name,
        ),
        download=service_bus_client.get_queue_receiver(
            queue_name=settings.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE,
        ),
        extraction=service_bus_client.get_queue_receiver(
            queue_name=settings.AZURE_SERVICE_BUS_EXTRACT_QUEUE,
        ),
        chunking=service_bus_client.get_queue_receiver(
            queue_name=settings.AZURE_SERVICE_BUS_CHUNK_QUEUE,
        ),
        embedding=service_bus_client.get_queue_receiver(
            queue_name=settings.AZURE_SERVICE_BUS_EMBED_QUEUE,
        ),
        classification=service_bus_client.get_queue_receiver(
            queue_name=settings.AZURE_SERVICE_BUS_CLASSIFY_QUEUE,
        ),
        discovery_sender=service_bus_client.get_queue_sender(
            queue_name=discovery_queue_name,
        ),
        download_sender=service_bus_client.get_queue_sender(
            queue_name=settings.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE,
        ),
        extraction_sender=service_bus_client.get_queue_sender(
            queue_name=settings.AZURE_SERVICE_BUS_EXTRACT_QUEUE,
        ),
        chunking_sender=service_bus_client.get_queue_sender(
            queue_name=settings.AZURE_SERVICE_BUS_CHUNK_QUEUE,
        ),
        embedding_sender=service_bus_client.get_queue_sender(
            queue_name=settings.AZURE_SERVICE_BUS_EMBED_QUEUE,
        ),
        classification_sender=service_bus_client.get_queue_sender(
            queue_name=settings.AZURE_SERVICE_BUS_CLASSIFY_QUEUE,
        ),
    )


def create_ingest_dispatchers(
    clients: IngestQueueClients,
) -> IngestDispatchers:

    return IngestDispatchers(
        discovery=AzureDiscoveryDispatcher(
            clients.discovery_sender,
        ),
        download=AzureDownloadDispatcher(
            clients.download_sender,
        ),
        extraction=AzureExtractionDispatcher(
            clients.extraction_sender,
        ),
        chunking=AzureChunkingDispatcher(
            clients.chunking_sender,
        ),
        embedding=AzureEmbeddingDispatcher(
            clients.embedding_sender,
        ),
        classification=AzureClassificationDispatcher(
            clients.classification_sender,
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
        clients.discovery_sender,
        clients.download_sender,
        clients.extraction_sender,
        clients.chunking_sender,
        clients.embedding_sender,
        clients.classification_sender,
        clients.service_bus_client,
    ):
        close = getattr(
            resource,
            "close",
            None,
        )

        if close is not None:
            await close()

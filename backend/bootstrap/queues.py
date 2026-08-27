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
    discovery: object
    download: object
    extraction: object
    chunking: object
    embedding: object
    classification: object


@dataclass(frozen=True)
class IngestDispatchers:
    discovery: AzureDiscoveryDispatcher
    download: AzureDownloadDispatcher
    extraction: AzureExtractionDispatcher
    chunking: AzureChunkingDispatcher
    embedding: AzureEmbeddingDispatcher
    classification: AzureClassificationDispatcher


def create_queue_client(
    queue_name: str,
):

    from azure.storage.queue.aio import QueueClient

    if not settings.AZURE_SERVICE_BUS_CONNECTION_STRING:
        raise RuntimeError(
            "AZURE_SERVICE_BUS_CONNECTION_STRING is required"
        )

    return QueueClient.from_connection_string(
        conn_str=(
            settings
            .AZURE_SERVICE_BUS_CONNECTION_STRING
        ),
        queue_name=queue_name,
    )


def create_ingest_queue_clients() -> IngestQueueClients:

    return IngestQueueClients(
        discovery=create_queue_client(
            settings.AZURE_SERVICE_BUS_QUEUE_NAME
            or settings.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE,
        ),
        download=create_queue_client(
            settings.AZURE_SERVICE_BUS_DOWNLOAD_QUEUE,
        ),
        extraction=create_queue_client(
            settings.AZURE_SERVICE_BUS_EXTRACT_QUEUE,
        ),
        chunking=create_queue_client(
            settings.AZURE_SERVICE_BUS_CHUNK_QUEUE,
        ),
        embedding=create_queue_client(
            settings.AZURE_SERVICE_BUS_EMBED_QUEUE,
        ),
        classification=create_queue_client(
            settings.AZURE_SERVICE_BUS_CLASSIFY_QUEUE,
        ),
    )


def create_ingest_dispatchers(
    clients: IngestQueueClients,
) -> IngestDispatchers:

    return IngestDispatchers(
        discovery=AzureDiscoveryDispatcher(
            clients.discovery,
        ),
        download=AzureDownloadDispatcher(
            clients.download,
        ),
        extraction=AzureExtractionDispatcher(
            clients.extraction,
        ),
        chunking=AzureChunkingDispatcher(
            clients.chunking,
        ),
        embedding=AzureEmbeddingDispatcher(
            clients.embedding,
        ),
        classification=AzureClassificationDispatcher(
            clients.classification,
        ),
    )

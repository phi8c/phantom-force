from app.application.chunking.chunking_engine import (
    ChunkingEngine,
)

from app.application.chunking.strategies.auto_chunk_strategy import (
    AutoChunkStrategy,
)

from app.domain.services.chunk_batch_builder import (
    ChunkBatchBuilder,
)

from app.infrastructure.messaging.azure.azure_service_bus_embedding_dispatcher import (
    AzureServiceBusEmbeddingDispatcher,
)

from app.infrastructure.messaging.azure.azure_service_bus_classification_dispatcher import (
    AzureServiceBusClassificationDispatcher,
)

from app.infrastructure.providers.storage.supabase_chunk_storage import (
    SupabaseChunkStorage,
)

from app.shared.config.settings import (
    settings,
)

from app.workers.consumers.chunk_consumer import (
    ChunkConsumer,
)

from app.workers.workers.chunk_worker import (
    ChunkWorker,
)


def build_chunk_consumer() -> ChunkConsumer:

    chunking_engine = ChunkingEngine(
        strategy=AutoChunkStrategy(
            level=3,
            max_chunk_tokens=800,
        )
    )

    embedding_dispatcher = (
        AzureServiceBusEmbeddingDispatcher(
            connection_string=(
                settings.AZURE_SERVICE_BUS_CONNECTION_STRING
            ),
            queue_name=(
                settings.AZURE_SERVICE_BUS_EMBED_QUEUE
            ),
        )
    )

    classification_dispatcher = (
        AzureServiceBusClassificationDispatcher(
            connection_string=(
                settings.AZURE_SERVICE_BUS_CONNECTION_STRING
            ),
            queue_name=(
                settings.AZURE_SERVICE_BUS_CLASSIFY_QUEUE
            ),
        )
    )

    chunk_worker = ChunkWorker(
        chunking_engine=chunking_engine,
        chunk_batch_builder=ChunkBatchBuilder(),
        chunk_storage=SupabaseChunkStorage(),
        embedding_dispatcher=embedding_dispatcher,
        classification_dispatcher=classification_dispatcher,
    )

    return ChunkConsumer(
        chunk_worker=chunk_worker,
    )
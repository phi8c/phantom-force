from app.infrastructure.messaging.azure.azure_service_bus_chunk_dispatcher import (
    AzureServiceBusChunkDispatcher,
)

from app.shared.config.settings import (
    settings,
)

from app.workers.consumers.save_extraction_db_consumer import (
    SaveExtractionDbConsumer,
)

from app.workers.workers.save_extraction_db_worker import (
    SaveExtractionDbWorker,
)


def build_save_extraction_consumer():

    chunk_dispatcher = (
        AzureServiceBusChunkDispatcher(
            connection_string=(
                settings.AZURE_SERVICE_BUS_CONNECTION_STRING
            ),
            queue_name=(
                settings.AZURE_SERVICE_BUS_CHUNK_QUEUE
            ),
        )
    )

    worker = (
        SaveExtractionDbWorker(
            chunk_dispatcher=(
                chunk_dispatcher
            ),
        )
    )

    return SaveExtractionDbConsumer(
        save_extraction_worker=worker,
    )
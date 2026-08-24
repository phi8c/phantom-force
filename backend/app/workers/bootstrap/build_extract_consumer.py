from app.shared.config.settings import (
    settings,
)

from app.domain.ports.storage.extract.supabase.supabase_original_file_storage import (
    SupabaseOriginalFileStorage,
)

from app.infrastructure.providers.storage.local_temp_storage import (
    LocalTempStorage,
)

from app.infrastructure.providers.extraction.docling.docling_extractor import (
    DoclingExtractor,
)

from app.workers.dispatchers.local_save_extraction_dispatcher import (
    LocalSaveExtractionDispatcher,
)

from app.workers.consumers.extract_consumer import (
    ExtractConsumer,
)

from app.workers.workers.extract_worker import (
    ExtractWorker,
)


def build_extract_consumer():

    extractor = (
        DoclingExtractor()
    )

    original_file_storage = (
        SupabaseOriginalFileStorage()
    )

    temp_storage = (
        LocalTempStorage()
    )

    save_extraction_dispatcher = (
        LocalSaveExtractionDispatcher()
    )

    extract_worker = (
        ExtractWorker(
            extractor=extractor,
            original_file_storage=(
                original_file_storage
            ),
            temp_storage=(
                temp_storage
            ),
            save_extraction_dispatcher=(
                save_extraction_dispatcher
            ),
        )
    )

    return ExtractConsumer(
        connection_string=(
            settings.AZURE_SERVICE_BUS_CONNECTION_STRING
        ),
        queue_name=(
            settings.AZURE_SERVICE_BUS_EXTRACT_QUEUE
        ),
        extract_worker=(
            extract_worker
        ),
    )
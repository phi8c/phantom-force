from app.infrastructure.providers.storage.supabase_extraction_storage import (
    SupabaseExtractionStorage,
)

from app.domain.ports.storage.extract.supabase.extraction_storage import (
    ExtractionStorage,
)

from app.workers.consumers.save_extraction_storage_consumer import (
    SaveExtractionStorageConsumer,
)

from app.workers.workers.save_extraction_storage_worker import (
    SaveExtractionStorageWorker,
)

from app.domain.ports.storage.extract.supabase.supabase_storage import (
    SupabaseStorage,)



def build_save_extraction_storage_consumer():

    extraction_storage = (
        SupabaseStorage()
    )

    worker = (
        SaveExtractionStorageWorker(
            extraction_storage=(
                extraction_storage
            )
        )
    )

    return (
        SaveExtractionStorageConsumer(
            save_extraction_worker=(
                worker
            )
        )
    )
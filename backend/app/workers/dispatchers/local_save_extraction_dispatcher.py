from app.shared.queue.queue_manager import (
    queue_manager,
)

from app.workers.dispatchers.local_save_extraction_storage_dispatcher import (
    LocalSaveExtractionStorageDispatcher,
)


class LocalSaveExtractionDispatcher:

    def __init__(
        self,
    ):
        self.storage_dispatcher = (
            LocalSaveExtractionStorageDispatcher()
        )

    async def dispatch(
        self,
        message,
    ):

        db_queue = (
            queue_manager.get_queue(
                "save_extraction_db"
            )
        )

        await (
            db_queue.enqueue(
                message
            )
        )

        await (
            self.storage_dispatcher.dispatch(
                message
            )
        )
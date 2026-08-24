from app.shared.queue.queue_manager import (
    queue_manager,
)


class LocalSaveExtractionStorageDispatcher:

    async def dispatch(
        self,
        message,
    ):

        queue = (
            queue_manager.get_queue(
                "save_extraction_storage"
            )
        )

        await (
            queue.enqueue(
                message
            )
        )
from app.shared.queue.queue_manager import (
    queue_manager,
)


class SaveExtractionStorageConsumer:

    def __init__(
        self,
        save_extraction_worker,
    ):
        self.save_extraction_worker = (
            save_extraction_worker
        )

    async def start(
        self,
    ):

        queue = (
            queue_manager.get_queue(
                "save_extraction_storage"
            )
        )

        while True:

            message = await (
                queue.dequeue()
            )

            await (
                self.save_extraction_worker.execute(
                    message,
                )
            )
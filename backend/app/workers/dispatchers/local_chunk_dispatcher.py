from app.application.ingestion.messages.chunk_message import (
    ChunkMessage,
)

from app.shared.queue.queue_manager import (
    queue_manager,
)


class LocalChunkDispatcher:

    async def dispatch(
        self,
        message: ChunkMessage,
    ) -> None:

        queue = (
            queue_manager.get_queue(
                "chunk",
            )
        )

        await queue.enqueue(
            message,
        )
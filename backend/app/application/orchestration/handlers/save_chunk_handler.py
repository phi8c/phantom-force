from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.events.chunk_created_event import (
    ChunkCreatedEvent,
)


class SaveChunkHandler(
    EventHandler,
):

    def __init__(
        self,
        chunk_repository,
    ):
        self.chunk_repository = (
            chunk_repository
        )

    async def handle(
        self,
        event: ChunkCreatedEvent,
    ) -> None:

        for chunk in event.chunks:

            await (
                self.chunk_repository.create(
                    chunk,
                )
            )
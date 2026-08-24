from app.application.orchestration.contracts.event_bus import (
    EventBus,
)

from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.events.chunk_created_event import (
    ChunkCreatedEvent,
)

from app.domain.events.embedding_completed_event import (
    EmbeddingCompletedEvent,
)


class EmbedHandler(
    EventHandler,
):

    def __init__(
        self,
        embedding_provider,
        event_bus: EventBus,
    ):
        self.embedding_provider = (
            embedding_provider
        )

        self.event_bus = (
            event_bus
        )

    async def handle(
        self,
        event: ChunkCreatedEvent,
    ) -> None:

        embeddings = await (
            self.embedding_provider.embed(
                event.chunks,
            )
        )

        await self.event_bus.publish(
            EmbeddingCompletedEvent.create(
                document_id=(
                    event.document_id
                ),
                embeddings=embeddings,
            )
        )
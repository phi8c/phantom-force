from app.application.orchestration.contracts.event_bus import (
    EventBus,
)

from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.events.chunk_created_event import (
    ChunkCreatedEvent,
)

from app.domain.events.document_extracted_event import (
    DocumentExtractedEvent,
)


class ChunkHandler(
    EventHandler,
):

    def __init__(
        self,
        chunking_engine,
        event_bus: EventBus,
    ):
        self.chunking_engine = (
            chunking_engine
        )

        self.event_bus = (
            event_bus
        )

    async def handle(
        self,
        event: DocumentExtractedEvent,
    ) -> None:

        chunks = list(
            self.chunking_engine.chunk(
                event.extraction,
            )
        )

        await self.event_bus.publish(
            ChunkCreatedEvent.create(
                document_id=(
                    event.document_id
                ),
                chunks=chunks,
            )
        )
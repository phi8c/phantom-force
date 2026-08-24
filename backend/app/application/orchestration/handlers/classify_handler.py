from app.application.orchestration.contracts.event_bus import (
    EventBus,
)

from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.events.chunk_created_event import (
    ChunkCreatedEvent,
)

from app.domain.events.classification_completed_event import (
    ClassificationCompletedEvent,
)


class ClassifyHandler(
    EventHandler,
):

    def __init__(
        self,
        classifier,
        event_bus: EventBus,
    ):
        self.classifier = classifier

        self.event_bus = event_bus

    async def handle(
        self,
        event: ChunkCreatedEvent,
    ) -> None:

        labels = await (
            self.classifier.classify(
                event.chunks,
            )
        )

        await self.event_bus.publish(
            ClassificationCompletedEvent.create(
                document_id=(
                    event.document_id
                ),
                labels=labels,
            )
        )
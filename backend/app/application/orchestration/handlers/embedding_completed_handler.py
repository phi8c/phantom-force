from app.application.orchestration.contracts.event_bus import (
    EventBus,
)

from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.events.document_ready_for_index_event import (
    DocumentReadyForIndexEvent,
)

from app.domain.events.embedding_completed_event import (
    EmbeddingCompletedEvent,
)


class EmbeddingCompletedHandler(
    EventHandler,
):

    def __init__(
        self,
        state_repository,
        event_bus: EventBus,
    ):
        self.state_repository = (
            state_repository
        )

        self.event_bus = (
            event_bus
        )

    async def handle(
        self,
        event: EmbeddingCompletedEvent,
    ) -> None:

        state = await (
            self.state_repository
            .get_by_document_id(
                event.document_id,
            )
        )

        if not state:
            return

        state.embeddings = (
            event.embeddings
        )

        state.embedding_ready = (
            True
        )

        await (
            self.state_repository.update(
                state,
            )
        )

        if (
            state.classification_ready
            and state.embedding_ready
            and not state.index_event_published
        ):

            state.index_event_published = (
                True
            )

            await (
                self.state_repository.update(
                    state,
                )
            )

            await self.event_bus.publish(
                DocumentReadyForIndexEvent.create(
                    document_id=(
                        state.document_id
                    ),
                )
            )
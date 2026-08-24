from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.application.orchestration.serializers.chunk_serializer import (
    ChunkSerializer,
)

from app.domain.entities.document_pipeline_state import (
    DocumentPipelineState,
)

from app.domain.events.chunk_created_event import (
    ChunkCreatedEvent,
)


class ChunkCreatedStateHandler(
    EventHandler,
):

    def __init__(
        self,
        state_repository,
    ):
        self.state_repository = (
            state_repository
        )

    async def handle(
        self,
        event: ChunkCreatedEvent,
    ) -> None:

        state = await (
            self.state_repository
            .get_by_document_id(
                event.document_id,
            )
        )

        serialized_chunks = [
            ChunkSerializer.to_dict(
                chunk,
            )
            for chunk in event.chunks
        ]

        if not state:

            state = (
                DocumentPipelineState(
                    document_id=(
                        event.document_id
                    ),
                    chunks=(
                        serialized_chunks
                    ),
                    labels=None,
                    embeddings=None,
                    chunks_ready=True,
                    classification_ready=False,
                    embedding_ready=False,
                    index_event_published=False,
                )
            )

            await (
                self.state_repository.create(
                    state,
                )
            )

            return

        state.chunks = (
            serialized_chunks
        )

        state.chunks_ready = True

        await (
            self.state_repository.update(
                state,
            )
        )
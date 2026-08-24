from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.events.document_ready_for_index_event import (
    DocumentReadyForIndexEvent,
)
from app.application.orchestration.serializers.chunk_serializer import ChunkSerializer


class DocumentReadyForIndexHandler(
    EventHandler,
):

    def __init__(
        self,
        state_repository,
        indexing_engine,
    ):
        self.state_repository = (
            state_repository
        )

        self.indexing_engine = (
            indexing_engine
        )

    async def handle(
        self,
        event: DocumentReadyForIndexEvent,
    ) -> None:

        state = await (
            self.state_repository
            .get_by_document_id(
                event.document_id,
            )
        )

        if not state:
            return

        await self.indexing_engine.index(
            chunks = [

    ChunkSerializer.from_dict(
        chunk,
    )

    for chunk in state.chunks
],
            labels=state.labels,
            embeddings=state.embeddings,
        )
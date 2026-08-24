from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base_event import (
    BaseEvent,
)


from app.domain.entities.chunk import (
    Chunk,
)


@dataclass(slots=True)
class ChunkCreatedEvent(
    BaseEvent,
):

    document_id: UUID

    chunks: list[Chunk]
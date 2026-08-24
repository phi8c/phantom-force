from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base_event import (
    BaseEvent,
)


@dataclass(slots=True)
class ChunkBatchReadyEvent(
    BaseEvent,
):

    document_id: UUID

    batch_id: UUID
from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base_event import (
    BaseEvent,
)


@dataclass(slots=True)
class DocumentReadyForIndexEvent(
    BaseEvent,
):

    document_id: UUID
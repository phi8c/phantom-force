from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.document_extraction import (
    DocumentExtraction,
)

from app.domain.events.base_event import (
    BaseEvent,
)


@dataclass(slots=True)
class DocumentExtractedEvent(
    BaseEvent,
):

    document_id: UUID

    extraction: DocumentExtraction
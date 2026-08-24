# app/domain/events/document_downloaded_event.py

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base_event import (
    BaseEvent,
)


@dataclass(slots=True)
class DocumentDownloadedEvent(
    BaseEvent,
):

    document_id: UUID

    temp_file_path: str
from datetime import datetime
from uuid import UUID

from app.domain.entities.chunk import Chunk
from app.domain.entities.document_extraction import DocumentExtraction
from app.domain.events.chunk_created_event import ChunkCreatedEvent
from app.domain.events.document_extracted_event import DocumentExtractedEvent


class EventDeserializer:

    def deserialize(self, event_class, payload: dict):
        payload = dict(payload)

        if payload.get("event_id"):
            payload["event_id"] = UUID(payload["event_id"])

        if payload.get("occurred_at"):
            payload["occurred_at"] = datetime.fromisoformat(payload["occurred_at"])

        if event_class is DocumentExtractedEvent:
            payload["extraction"] = self._deserialize_extraction(payload["extraction"])

        elif event_class is ChunkCreatedEvent:
            payload["chunks"] = [
                self._deserialize_chunk(chunk) for chunk in payload["chunks"]
            ]

        return event_class(**payload)

    def _deserialize_extraction(self, payload: dict) -> DocumentExtraction:
        return DocumentExtraction(
            id=UUID(payload["id"]) if payload.get("id") else None,
            document_id=UUID(payload["document_id"]),
            structured_content=payload["structured_content"],
            page_count=payload["page_count"],
            created_at=None,
        )

    def _deserialize_chunk(self, payload: dict) -> Chunk:
        return Chunk(
            document_id=UUID(payload["document_id"]),
            source_section_id=payload["source_section_id"],
            sequence=payload["sequence"],
            title=payload["title"],
            content=payload["content"],
            hierarchy_path=payload["hierarchy_path"],
            level=payload["level"],
            tables=payload["tables"],
            image_captions=payload["image_captions"],
            metadata=payload["metadata"],
        )
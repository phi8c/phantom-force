from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ChunkClassification:
    id: UUID | None
    chunk_id: UUID
    model_name: str
    label: str
    confidence: float | None
    raw_response: dict | None
    created_at: datetime | None

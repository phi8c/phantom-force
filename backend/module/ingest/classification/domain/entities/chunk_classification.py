from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ChunkClassification:
    id: UUID | None
    batch_id: UUID
    chunk_id: UUID
    sensitivity: int
    metadata: dict
    created_at: datetime | None
    updated_at: datetime | None

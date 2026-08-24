from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass, field



@dataclass
class DocumentChunk:

    id: UUID | None

    batch_id: UUID | None

    document_id: UUID

    chunk_index: int

    title: str | None

    content: str

    metadata: dict

    created_at: datetime = field(
    default_factory=lambda: datetime.now(timezone.utc)
)
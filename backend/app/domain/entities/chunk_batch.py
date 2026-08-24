from dataclasses import dataclass

from uuid import UUID
from datetime import datetime
from datetime import timezone
from dataclasses import field



@dataclass
class ChunkBatch:

    id: UUID | None

    document_id: UUID

    batch_index: int
    total_chunks: int
    
    created_at: datetime = field(
    default_factory=lambda: datetime.now(timezone.utc),
)
    
    classification_completed: bool = False

    embedding_completed: bool = False

    batch_completed: bool = False

   
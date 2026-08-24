from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DocumentChunkEmbedding:

    id: UUID | None

    chunk_id: UUID

    model_name: str

    embedding: list[float]

    dimension: int

    token_count: int | None

    created_at: datetime | None
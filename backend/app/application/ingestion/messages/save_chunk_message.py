from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.chunk import (
    Chunk,
)


@dataclass(
    slots=True,
)
class SaveChunkMessage:

    document_id: UUID

    chunks: list[Chunk]
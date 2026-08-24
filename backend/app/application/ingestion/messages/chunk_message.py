from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class ChunkMessage:

    document_id: UUID

    extraction_id: UUID
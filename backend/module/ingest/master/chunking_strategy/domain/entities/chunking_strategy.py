from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ChunkingStrategy:

    id: UUID | None

    code: str

    name: str

    configuration: dict

    enabled: bool

    created_at: datetime | None

    updated_at: datetime | None
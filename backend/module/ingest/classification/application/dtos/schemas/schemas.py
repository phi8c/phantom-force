from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class Chunk:
    id: UUID
    content: str
    metadata: dict[str, Any]
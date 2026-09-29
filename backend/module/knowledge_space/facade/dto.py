from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeSpaceDTO:
    id: UUID
    status: str

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeSpaceResponse:
    id: UUID
    enterprise_id: UUID
    name: str
    code: str
    description: str | None
    status: str
    configuration: dict
    created_at: datetime | None
    updated_at: datetime | None

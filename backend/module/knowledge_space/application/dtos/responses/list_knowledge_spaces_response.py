from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeSpaceListItemResponse:
    id: UUID
    enterprise_id: UUID
    enterprise_name: str
    name: str
    code: str
    description: str | None
    status: str
    created_at: datetime | None


@dataclass(frozen=True)
class ListKnowledgeSpacesResponse:
    items: list[KnowledgeSpaceListItemResponse]
    page: int
    page_size: int
    total: int

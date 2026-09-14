from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListKnowledgeSpacesRequest:
    page: int = 1
    page_size: int = 20
    enterprise_id: UUID | None = None
    search: str | None = None
    status: str | None = None

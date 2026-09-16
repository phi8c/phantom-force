from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ListIngestionJobsQuery:
    knowledge_space_id: UUID | None
    status: str | None
    limit: int
    cursor: str | None


@dataclass(frozen=True)
class IngestionJobListItem:
    id: UUID
    knowledge_space_id: UUID
    trigger_type: str
    status: str | None
    is_build_graph: bool
    total_files: int
    completed_files: int
    failed_files: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime | None
    scope_type: str | None
    scope_data: dict | None


@dataclass(frozen=True)
class ListIngestionJobsResult:
    items: list[IngestionJobListItem]
    next_cursor: str | None
    has_more: bool

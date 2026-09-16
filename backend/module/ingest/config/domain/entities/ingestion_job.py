from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class IngestionJob:

    id: UUID | None

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

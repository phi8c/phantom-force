from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums.ingestion_status import (
    IngestionStatus,
)


@dataclass
class IngestionRun:

    id: UUID | None

    source_id: UUID

    trigger_type: str

    scope_type: str

    scope_data: dict | None

    status: IngestionStatus

    is_build_graph: bool

    total_files: int

    completed_files: int

    failed_files: int
    configuration: dict

    started_at: datetime | None

    finished_at: datetime | None

    created_at: datetime | None
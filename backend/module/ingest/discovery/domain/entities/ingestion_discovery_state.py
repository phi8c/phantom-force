from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class IngestionDiscoveryState:
    ingestion_job_id: UUID

    cursor: dict | None

    completed: bool

    discovered_files: int

    created_at: datetime | None

    updated_at: datetime | None
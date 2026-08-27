from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.ingest.download.domain.enums.task_status import (
    TaskStatus,
)


@dataclass
class DownloadTask:
    id: UUID | None

    ingestion_job_id: UUID
    document_id: UUID

    status: TaskStatus

    attempt_count: int

    claimed_by: str | None
    lease_until: datetime | None

    error: str | None

    created_at: datetime | None
    updated_at: datetime | None
    completed_at: datetime | None
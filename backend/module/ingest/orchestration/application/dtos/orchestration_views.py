from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class StageCount:
    stage: str
    status: str
    count: int


@dataclass(frozen=True)
class BatchSummary:
    id: UUID
    batch_index: int
    status: str
    total_files: int
    completed_files: int
    failed_files: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BatchDocumentView:
    document_id: UUID
    ordinal: int | None
    file_name: str
    file_extension: str | None
    file_size_bytes: int | None
    stages: list["DocumentStageStateView"]


@dataclass(frozen=True)
class DocumentStageStateView:
    document_id: UUID
    stage: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error: str | None


@dataclass(frozen=True)
class OrchestrationEventView:
    sequence_no: int
    ingestion_job_id: UUID
    ingestion_batch_id: UUID | None
    document_id: UUID | None
    event_type: str
    stage: str | None
    status: str | None
    payload: dict
    created_at: datetime

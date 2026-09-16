from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SaveIngestionJobScopeCommand:
    ingestion_job_id: UUID
    scope_type: str
    scope_data: dict


@dataclass(frozen=True)
class IngestionJobScopeResponse:
    ingestion_job_id: UUID
    scope_type: str | None
    scope_data: dict | None


@dataclass(frozen=True)
class IngestionJobScopeEnvelope:
    configured: bool
    data: IngestionJobScopeResponse | None

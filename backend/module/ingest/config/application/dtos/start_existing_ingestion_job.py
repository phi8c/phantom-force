from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class StartExistingIngestionJobCommand:
    ingestion_job_id: UUID
    batch_size: int


@dataclass(frozen=True)
class StartExistingIngestionJobResult:
    ingestion_job_id: UUID
    status: str

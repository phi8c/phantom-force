from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SaveIngestionJobConfigurationCommand:
    ingestion_job_id: UUID
    extraction_engine_code: str
    chunking_strategy_code: str
    model_set_code: str | None = None
    is_classification: bool = False
    configuration: dict | None = None


@dataclass(frozen=True)
class IngestionJobConfigurationResponse:
    id: UUID
    ingestion_job_id: UUID
    is_classification: bool
    model_set_id: UUID | None
    chunking_strategy_id: UUID
    extraction_engine_id: UUID
    configuration: dict
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class IngestionJobConfigurationEnvelope:
    configured: bool
    data: IngestionJobConfigurationResponse | None

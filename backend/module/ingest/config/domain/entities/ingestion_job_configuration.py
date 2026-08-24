from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class IngestionJobConfiguration:

    id: UUID | None

    ingestion_job_id: UUID

    is_classification: bool

    model_set_id: UUID | None

    chunking_strategy_id: UUID

    extraction_engine_id: UUID

    configuration: dict

    created_at: datetime | None

    updated_at: datetime | None
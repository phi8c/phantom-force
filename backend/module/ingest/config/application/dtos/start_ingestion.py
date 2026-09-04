from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class StartIngestionCommand:

    knowledge_space_id: UUID

    extraction_engine_code: str

    chunking_strategy_code: str

    model_set_code: str | None

    is_classification: bool

    trigger_type: str

    scope_type: str | None

    scope_data: dict[str, Any] | None

    configuration: dict[str, Any] | None

    is_build_graph: bool

    batch_size: int


@dataclass(frozen=True)
class StartIngestionResult:

    ingestion_job_id: UUID

    status: str

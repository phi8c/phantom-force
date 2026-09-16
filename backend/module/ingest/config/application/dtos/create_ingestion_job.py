from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateIngestionJobCommand:
    knowledge_space_id: UUID
    trigger_type: str = "MANUAL"
    is_build_graph: bool = False


@dataclass(frozen=True)
class CreateIngestionJobResult:
    ingestion_job_id: UUID

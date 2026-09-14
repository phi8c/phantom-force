from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DiscoveryBatchCreationResult:
    ingestion_batch_id: UUID
    created: bool

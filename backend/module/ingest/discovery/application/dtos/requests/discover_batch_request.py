from dataclasses import dataclass
from uuid import UUID


@dataclass
class DiscoverBatchRequest:
    ingestion_job_id: UUID
    batch_size: int
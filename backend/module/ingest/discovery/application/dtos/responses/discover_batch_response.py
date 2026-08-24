from dataclasses import dataclass
from uuid import UUID


@dataclass
class DiscoveryItem:
    document_id: UUID
    external_file_id: str
    file_name: str


@dataclass
class DiscoverBatchResponse:
    ingestion_job_id: UUID
    items: list[DiscoveryItem]
    has_more: bool
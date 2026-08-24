from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.ingest.discovery.domain.enums.ingestion_document_status import (
    IngestionDocumentStatus,
)


@dataclass
class IngestionDocumentState:
    document_id: UUID
    ingestion_job_id: UUID
    status: IngestionDocumentStatus
    created_at: datetime | None
    updated_at: datetime | None
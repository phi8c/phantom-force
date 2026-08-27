from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DocumentExtraction:
    id: UUID | None
    document_id: UUID
    structured_content: dict
    page_count: int | None
    created_at: datetime | None

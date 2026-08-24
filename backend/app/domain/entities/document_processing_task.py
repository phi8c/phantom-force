from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DocumentProcessingTask:

    id: UUID | None

    document_id: UUID
    
    batch_id: UUID  

    task_type: str

    status: str

    retry_count: int

    error_message: str | None

    started_at: datetime | None

    finished_at: datetime | None

    created_at: datetime | None

    updated_at: datetime | None
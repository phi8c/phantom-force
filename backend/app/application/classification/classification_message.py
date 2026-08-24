from dataclasses import dataclass
from uuid import UUID

@dataclass(slots=True)
class ClassificationMessage:
    task_id: UUID
    document_id: UUID
    batch_id: UUID
from dataclasses import dataclass
from uuid import UUID


@dataclass(
    slots=True,
    frozen=True,
)
class EmbeddingMessage:

    task_id: UUID

    document_id: UUID

    batch_id: UUID
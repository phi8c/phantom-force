from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeWriteRequest:
    knowledge_space_id: UUID
    document_id: UUID
    chunk_id: UUID
    model_name: str
    raw_response: dict[str, Any]
    document_context: Any | None = None

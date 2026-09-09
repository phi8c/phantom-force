from dataclasses import dataclass
from typing import Any
from uuid import UUID

from module.ingest.knowledge.application.dtos.knowledge_document_context import (
    KnowledgeDocumentContext,
)


@dataclass(frozen=True)
class KnowledgeWriteRequest:
    knowledge_space_id: UUID
    document_id: UUID
    chunk_id: UUID
    model_name: str
    raw_response: dict[str, Any]
    document_context: KnowledgeDocumentContext | None = None

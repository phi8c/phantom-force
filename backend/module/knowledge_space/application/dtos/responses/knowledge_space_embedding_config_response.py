from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeSpaceEmbeddingConfigResponse:
    id: UUID
    knowledge_space_id: UUID
    embedding_model_id: UUID
    configuration: dict
    enabled: bool
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class KnowledgeSpaceEmbeddingConfigEnvelopeResponse:
    configured: bool
    data: KnowledgeSpaceEmbeddingConfigResponse | None

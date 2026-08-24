from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class KnowledgeSpaceEmbeddingConfig:

    id: UUID | None

    knowledge_space_id: UUID

    embedding_model_id: UUID

    configuration: dict

    enabled: bool

    created_at: datetime | None

    updated_at: datetime | None
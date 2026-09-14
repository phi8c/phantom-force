from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SaveEmbeddingConfigRequest:
    embedding_model_id: UUID
    configuration: dict
    enabled: bool = True

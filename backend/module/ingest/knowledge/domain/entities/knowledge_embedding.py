from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class KnowledgeRegistryEmbeddingKind(str, Enum):
    DOCUMENT_TYPE = "document_type"
    TOPIC = "topic"
    OBJECT = "object"
    IDENTIFIER = "identifier"
    INFORMATION_TYPE = "information_type"
    INFORMATION_FIELD = "information_field"


@dataclass(frozen=True)
class KnowledgeRegistryEmbeddingTarget:
    kind: KnowledgeRegistryEmbeddingKind
    id: UUID
    text: str


@dataclass(frozen=True)
class KnowledgeRegistryEmbeddingUpdate:
    kind: KnowledgeRegistryEmbeddingKind
    id: UUID
    embedding: list[float]


@dataclass(frozen=True)
class KnowledgeSemanticRequestVectors:
    request_id: str
    document_type_vectors: dict[str, list[float]] | None = None
    topic_vectors: dict[str, list[float]] | None = None
    object_vectors: dict[str, list[float]] | None = None
    identifier_vectors: dict[str, list[float]] | None = None
    information_type_vectors: dict[str, list[float]] | None = None
    information_field_vectors: dict[str, list[float]] | None = None

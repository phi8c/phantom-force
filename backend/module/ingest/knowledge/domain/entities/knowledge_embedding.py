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
class KnowledgeSemanticSeedVectors:
    seed_id: str
    document_type_vectors: dict[str, list[float]] | None = None
    topic_vectors: dict[str, list[float]] | None = None
    object_vectors: dict[str, list[float]] | None = None
    identifier_vectors: dict[str, list[float]] | None = None
    information_type_vectors: dict[str, list[float]] | None = None
    information_field_vectors: dict[str, list[float]] | None = None

    @property
    def request_id(self) -> str:
        return self.seed_id

    @property
    def object_vector(self) -> list[float] | None:
        vectors = self.object_vectors or {}
        return next(iter(vectors.values()), None)

    @property
    def identifier_vector(self) -> list[float] | None:
        vectors = self.identifier_vectors or {}
        return next(iter(vectors.values()), None)

    @property
    def information_type_vector(self) -> list[float] | None:
        vectors = self.information_type_vectors or {}
        return next(iter(vectors.values()), None)


@dataclass(frozen=True)
class LegacyKnowledgeSemanticSeedVectors:
    seed_id: str
    object_vector: list[float] | None = None
    identifier_vector: list[float] | None = None
    information_type_vector: list[float] | None = None
    topic_vectors: dict[str, list[float]] | None = None

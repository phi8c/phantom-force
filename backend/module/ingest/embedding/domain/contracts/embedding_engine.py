from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from uuid import UUID

from module.ingest.embedding.domain.contracts.chunk_reader import (
    ChunkForEmbedding,
)


@dataclass(frozen=True)
class EmbeddingResult:
    chunk_id: UUID
    vector: list[float] | None
    model_name: str
    dimension: int | None
    token_count: int | None
    status: str
    error_message: str | None


class EmbeddingEngine(ABC):

    @abstractmethod
    async def embed_batch(
        self,
        chunks: list[ChunkForEmbedding],
    ) -> list[EmbeddingResult]:
        pass

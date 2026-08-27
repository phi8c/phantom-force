from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from uuid import UUID

from module.ingest.embedding.domain.entities.document_chunk_embedding import (
    DocumentChunkEmbedding,
)


class DocumentChunkEmbeddingRepository(ABC):

    @abstractmethod
    async def get_by_chunk_and_model(
        self,
        chunk_id: UUID,
        model_name: str,
    ) -> DocumentChunkEmbedding | None:
        pass

    @abstractmethod
    async def upsert_many(
        self,
        embeddings: Iterable[DocumentChunkEmbedding],
    ) -> list[DocumentChunkEmbedding]:
        pass

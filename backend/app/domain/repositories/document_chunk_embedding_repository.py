from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.document_chunk_embedding import (
    DocumentChunkEmbedding,
)


class DocumentChunkEmbeddingRepository(
    ABC,
):

    @abstractmethod
    async def create(
        self,
        embedding: DocumentChunkEmbedding,
    ) -> DocumentChunkEmbedding:
        ...

    @abstractmethod
    async def create_many(
        self,
        embeddings: list[
            DocumentChunkEmbedding
        ],
    ) -> list[DocumentChunkEmbedding]:
        ...

    @abstractmethod
    async def update(
        self,
        embedding: DocumentChunkEmbedding,
    ) -> DocumentChunkEmbedding:
        ...

    @abstractmethod
    async def get_by_chunk_and_model(
        self,
        chunk_id: UUID,
        model_name: str,
    ) -> DocumentChunkEmbedding | None:
        ...

    @abstractmethod
    async def list_by_chunk_id(
        self,
        chunk_id: UUID,
    ) -> list[DocumentChunkEmbedding]:
        ...
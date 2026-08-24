from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.document_chunk import (
    DocumentChunk,
)


class DocumentChunkRepository(
    ABC,
):

    @abstractmethod
    async def create(
        self,
        chunk: DocumentChunk,
    ) -> DocumentChunk:
        ...

    @abstractmethod
    async def create_many(
        self,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunk]:
        ...

    @abstractmethod
    async def get_by_id(
        self,
        chunk_id: UUID,
    ) -> DocumentChunk | None:
        ...

    @abstractmethod
    async def list_by_batch_id(
        self,
        batch_id: UUID,
    ) -> list[DocumentChunk]:
        ...

    @abstractmethod
    async def list_by_document_id(
        self,
        document_id: UUID,
    ) -> list[DocumentChunk]:
        ...
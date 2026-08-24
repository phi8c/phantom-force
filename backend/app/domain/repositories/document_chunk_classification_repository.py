from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.document_chunk_classification import (
    DocumentChunkClassification,
)


class DocumentChunkClassificationRepository(
    ABC,
):

    @abstractmethod
    async def create(
        self,
        classification: DocumentChunkClassification,
    ) -> DocumentChunkClassification:
        ...

    @abstractmethod
    async def create_many(
        self,
        classifications: list[
            DocumentChunkClassification
        ],
    ) -> list[DocumentChunkClassification]:
        ...

    @abstractmethod
    async def list_by_chunk_id(
        self,
        chunk_id: UUID,
    ) -> list[DocumentChunkClassification]:
        ...
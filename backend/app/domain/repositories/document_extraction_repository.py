from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.document_extraction import (
    DocumentExtraction,
)


class DocumentExtractionRepository(
    ABC,
):

    @abstractmethod
    async def create(
        self,
        extraction: DocumentExtraction,
    ) -> DocumentExtraction:
        ...

    @abstractmethod
    async def get_by_id(
        self,
        extraction_id: UUID,
    ) -> DocumentExtraction | None:
        ...

    @abstractmethod
    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentExtraction | None:
        ...
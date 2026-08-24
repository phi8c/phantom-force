from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.document import (
    Document,
)


class DocumentRepository(
    ABC,
):

    @abstractmethod 
    async def get_by_id(
        self,
        document_id: UUID,
    ) -> Document | None:
        pass

    @abstractmethod
    async def get_by_external_file_id(
        self,
        source_id: UUID,
        external_file_id: str,
    ) -> Document | None:
        pass

    @abstractmethod
    async def get_by_external_file_ids(
        self,
        source_id: UUID,
        external_file_ids: list[str],
    ) -> dict[str, Document]:
        pass

    @abstractmethod
    async def create(
        self,
        document: Document,
    ) -> Document:
        pass

    @abstractmethod
    async def update(
        self,
        document: Document,
    ) -> None:
        pass
from abc import ABC, abstractmethod
from uuid import UUID

from module.ingest.discovery.domain.entities.document import Document


class DocumentRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        document_id: UUID,
    ) -> Document | None:
        pass

    @abstractmethod
    async def get_by_external_file_id(
        self,
        data_hub_id: UUID,
        external_file_id: str,
    ) -> Document | None:
        pass

    @abstractmethod
    async def get_by_external_file_ids(
        self,
        data_hub_id: UUID,
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
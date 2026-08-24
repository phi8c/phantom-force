from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.discovery.domain.entities.ingestion_document_state import (
    IngestionDocumentState,
)


class IngestionDocumentStateRepository(
    ABC,
):

    @abstractmethod
    async def get_by_document_and_ingestion_job(
        self,
        document_id: UUID,
        ingestion_run_id: UUID,
    ) -> IngestionDocumentState | None:
        pass

    @abstractmethod
    async def create(
        self,
        state: IngestionDocumentState,
    ) -> IngestionDocumentState:
        pass

    @abstractmethod
    async def update(
        self,
        state: IngestionDocumentState,
    ) -> IngestionDocumentState:
        pass
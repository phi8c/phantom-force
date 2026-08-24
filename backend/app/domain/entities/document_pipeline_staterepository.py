from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.document_pipeline_state import (
    DocumentPipelineState,
)


class DocumentPipelineStateRepository(
    ABC,
):

    @abstractmethod
    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentPipelineState | None:
        pass

    @abstractmethod
    async def save(
        self,
        state: DocumentPipelineState,
    ) -> None:
        pass
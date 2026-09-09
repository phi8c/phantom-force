from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.classification.domain.entities.document_context import (
    DocumentContext,
)


class DocumentStructureAnalyzer(ABC):

    @abstractmethod
    async def analyze(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> DocumentContext:
        pass

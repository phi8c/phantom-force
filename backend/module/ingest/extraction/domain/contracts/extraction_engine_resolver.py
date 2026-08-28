from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.extraction.domain.contracts.extraction_engine import (
    ExtractionEngine,
)


class ExtractionEngineResolver(ABC):

    @abstractmethod
    async def resolve_for_job(
        self,
        ingestion_job_id: UUID,
    ) -> ExtractionEngine:
        pass

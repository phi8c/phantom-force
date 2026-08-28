from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.chunking.domain.contracts.chunking_engine import (
    ChunkingEngine,
)


class ChunkingEngineResolver(ABC):

    @abstractmethod
    async def resolve_for_job(
        self,
        ingestion_job_id: UUID,
    ) -> ChunkingEngine:
        pass

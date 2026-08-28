from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.embedding.domain.contracts.embedding_engine import (
    EmbeddingEngine,
)


class EmbeddingEngineResolver(ABC):

    @abstractmethod
    async def resolve_for_job(
        self,
        ingestion_job_id: UUID,
    ) -> EmbeddingEngine:
        pass

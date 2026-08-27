from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from module.ingest.chunking.domain.contracts.chunking_engine import (
    Chunk,
)


@dataclass(frozen=True)
class ChunkBatch:
    id: UUID
    ingestion_job_id: UUID
    document_id: UUID
    total_chunks: int


class ChunkBatchWriter(ABC):

    @abstractmethod
    async def get_by_job_and_document(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ChunkBatch | None:
        pass

    @abstractmethod
    async def create_with_chunks(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        chunks: Iterable[Chunk],
    ) -> ChunkBatch:
        pass

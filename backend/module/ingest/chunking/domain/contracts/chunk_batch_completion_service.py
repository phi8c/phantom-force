from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class BatchCompletionResult:
    dispatch_index: bool


class ChunkBatchCompletionService(ABC):

    @abstractmethod
    async def complete_embedding(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
    ) -> BatchCompletionResult:
        pass

    @abstractmethod
    async def complete_classification(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
    ) -> BatchCompletionResult:
        pass

    @abstractmethod
    async def mark_classification_completed(
        self,
        batch_id: UUID,
    ) -> None:
        pass

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class BatchFinalizationSignal:
    dispatch_index: bool


class BatchFinalizer(ABC):

    @abstractmethod
    async def complete_embedding(
        self,
        *,
        ingestion_job_id: UUID,
        batch_id: UUID,
    ) -> BatchFinalizationSignal:
        pass

    @abstractmethod
    async def dispatch_index(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        pass

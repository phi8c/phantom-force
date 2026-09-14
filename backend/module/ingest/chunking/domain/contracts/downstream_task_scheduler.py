from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DownstreamSignals:
    dispatch_embedding: bool
    dispatch_classification: bool
    classification_skipped: bool = False


class DownstreamTaskScheduler(ABC):

    @abstractmethod
    async def schedule(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        batch_id: UUID,
    ) -> DownstreamSignals:
        pass

    @abstractmethod
    async def dispatch_embedding(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        pass

    @abstractmethod
    async def dispatch_classification(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        pass

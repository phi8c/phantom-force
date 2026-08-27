from abc import ABC
from abc import abstractmethod
from uuid import UUID


class ExtractionTaskScheduler(ABC):

    @abstractmethod
    async def ensure_ready_task(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> None:
        pass

    @abstractmethod
    async def dispatch_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        pass

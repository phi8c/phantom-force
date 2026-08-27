from abc import ABC, abstractmethod
from uuid import UUID


class DownloadDispatcher(ABC):

    @abstractmethod
    async def dispatch(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        ...
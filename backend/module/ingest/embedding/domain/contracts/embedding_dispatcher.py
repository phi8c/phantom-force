from abc import ABC
from abc import abstractmethod
from uuid import UUID


class EmbeddingDispatcher(ABC):

    @abstractmethod
    async def dispatch_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        pass

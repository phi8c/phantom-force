from abc import ABC
from abc import abstractmethod
from uuid import UUID


class DiscoveryDispatcher(ABC):

    @abstractmethod
    async def dispatch(
        self,
        ingestion_job_id: UUID,
        batch_size: int,
    ) -> None:
        pass
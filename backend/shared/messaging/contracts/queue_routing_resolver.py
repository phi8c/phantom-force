from abc import ABC, abstractmethod
from uuid import UUID


class QueueRoutingResolver(ABC):
    @abstractmethod
    async def resolve_for_job(self, ingestion_job_id: UUID) -> str:
        raise NotImplementedError

from abc import ABC
from abc import abstractmethod
from uuid import UUID


class ExtractionDispatcher(ABC):

    @abstractmethod
    async def dispatch(
        self,
        ingestion_job_id: UUID,
    ) -> None:
        pass

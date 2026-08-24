from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)


class IngestionConfigRepository(ABC):

    @abstractmethod
    async def get_job_by_id(
        self,
        job_id: UUID,
    ) -> IngestionJob | None:
        pass

    @abstractmethod
    async def get_configuration_by_job_id(
        self,
        job_id: UUID,
    ) -> IngestionJobConfiguration | None:
        pass

    @abstractmethod
    async def get_job_with_configuration(
        self,
        job_id: UUID,
    ) -> tuple[
        IngestionJob,
        IngestionJobConfiguration,
    ] | None:
        pass
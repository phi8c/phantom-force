from abc import ABC
from abc import abstractmethod
from uuid import UUID
from dataclasses import dataclass

from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)
from module.ingest.config.domain.entities.ingestion_job_configuration import (
    IngestionJobConfiguration,
)


@dataclass(frozen=True)
class IngestionJobPage:
    items: list[IngestionJob]
    next_cursor: str | None
    has_more: bool


class IngestionConfigRepository(ABC):
    async def get_configuration_for_existing_job(self, job_id: UUID) -> IngestionJobConfiguration | None:
        if await self.get_job_by_id(job_id) is None:
            raise LookupError('ingestion_job_id was not found')
        return await self.get_configuration_by_job_id(job_id)

    @abstractmethod
    async def list_jobs(
        self,
        *,
        knowledge_space_id: UUID | None,
        status: str | None,
        limit: int,
        cursor: str | None,
    ) -> IngestionJobPage:
        pass


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

    @abstractmethod
    async def add_job(
        self,
        job: IngestionJob,
    ) -> IngestionJob:
        pass

    @abstractmethod
    async def add_configuration(
        self,
        configuration: IngestionJobConfiguration,
    ) -> IngestionJobConfiguration:
        pass

    @abstractmethod
    async def save_configuration(
        self,
        configuration: IngestionJobConfiguration,
    ) -> IngestionJobConfiguration:
        pass

    @abstractmethod
    async def update_job_scope(
        self,
        *,
        job_id: UUID,
        scope_type: str | None,
        scope_data: dict | None,
    ) -> IngestionJob:
        pass

    @abstractmethod
    async def mark_job_ready(
        self,
        *,
        job_id: UUID,
    ) -> IngestionJob:
        pass

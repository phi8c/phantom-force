from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.ingestion_run import (
    IngestionRun,
)


class IngestionRunRepository(
    ABC,
):

    @abstractmethod
    async def get_by_id(
        self,
        job_id: UUID,
    ) -> IngestionRun | None:
        pass

    @abstractmethod
    async def create(
        self,
        job: IngestionRun,
    ) -> IngestionRun:
        pass

    @abstractmethod
    async def update(
        self,
        job: IngestionRun,
    ) -> None:
        pass
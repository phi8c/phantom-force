from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.ingestion_source import (
    IngestionSource,
)


class SourceRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        source_id: UUID,
    ) -> IngestionSource | None:
        pass

    @abstractmethod
    async def get_enabled_sources(
        self,
    ) -> list[IngestionSource]:
        pass

    @abstractmethod
    async def create(
        self,
        source: IngestionSource,
    ) -> IngestionSource:
        pass

    @abstractmethod
    async def update(
        self,
        source: IngestionSource,
    ) -> None:
        pass
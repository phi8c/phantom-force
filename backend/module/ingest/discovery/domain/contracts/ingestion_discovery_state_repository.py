from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.discovery.domain.entities.ingestion_discovery_state import (
    IngestionDiscoveryState,
)


class IngestionDiscoveryStateRepository(
    ABC,
):

    @abstractmethod
    async def get_by_ingestion_job_id(
        self,
        ingestion_job_id: UUID,
    ) -> IngestionDiscoveryState | None:
        pass

    @abstractmethod
    async def save_progress(
        self,
        ingestion_job_id: UUID,
        cursor: dict | None,
        discovered_count: int,
        completed: bool,
    ) -> IngestionDiscoveryState:
        pass

    @abstractmethod
    async def complete(
        self,
        ingestion_job_id: UUID,
    ) -> IngestionDiscoveryState:
        pass
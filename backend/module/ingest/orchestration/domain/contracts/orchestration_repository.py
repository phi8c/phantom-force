from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ingest.orchestration.domain.enums import IngestionStage
from module.ingest.orchestration.domain.enums import OrchestrationEventType
from module.ingest.orchestration.domain.enums import StageStatus
from module.ingest.orchestration.domain.entities import (
    BatchStatusRefreshResult,
)
from module.ingest.orchestration.domain.entities import (
    DiscoveryBatchCreationResult,
)


class OrchestrationRepository(ABC):

    @abstractmethod
    async def create_discovery_batch(
        self,
        *,
        ingestion_job_id: UUID,
        document_ids: list[UUID],
    ) -> DiscoveryBatchCreationResult:
        raise NotImplementedError

    @abstractmethod
    async def find_batch_id_for_document(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> UUID | None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_stage_state(
        self,
        *,
        ingestion_job_id: UUID,
        ingestion_batch_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
        status: StageStatus,
        error: str | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def refresh_batch_status(
        self,
        *,
        ingestion_batch_id: UUID,
    ) -> BatchStatusRefreshResult:
        raise NotImplementedError

    @abstractmethod
    async def append_event(
        self,
        *,
        ingestion_job_id: UUID,
        event_type: OrchestrationEventType,
        ingestion_batch_id: UUID | None = None,
        document_id: UUID | None = None,
        stage: IngestionStage | None = None,
        status: StageStatus | None = None,
        payload: dict | None = None,
    ) -> None:
        raise NotImplementedError

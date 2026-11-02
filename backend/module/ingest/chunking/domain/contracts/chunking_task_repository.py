from abc import ABC
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from module.ingest.chunking.domain.entities.chunking_task import (
    ChunkingTask,
)


class ChunkingLeaseLostError(RuntimeError):
    pass


class ChunkingTaskRepository(ABC):
    @abstractmethod
    async def has_unfinished(self, ingestion_job_id: UUID) -> bool:
        pass

    @abstractmethod
    async def renew_lease(self, task_id: UUID, *, claimed_by: str, lease_until: datetime) -> bool:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        task_id: UUID,
    ) -> ChunkingTask | None:
        pass

    @abstractmethod
    async def get_by_job_and_document(
        self,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ChunkingTask | None:
        pass

    @abstractmethod
    async def create(
        self,
        task: ChunkingTask,
    ) -> ChunkingTask:
        pass

    @abstractmethod
    async def update(
        self,
        task: ChunkingTask,
    ) -> ChunkingTask:
        pass

    @abstractmethod
    async def claim_ready(
        self,
        ingestion_job_id: UUID,
        *,
        limit: int,
        claimed_by: str,
        lease_until: datetime,
    ) -> list[ChunkingTask]:
        pass

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from module.ingest.embedding.domain.entities.embedding_task import (
    EmbeddingTask,
)


class EmbeddingTaskRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        task_id: UUID,
    ) -> EmbeddingTask | None:
        pass

    @abstractmethod
    async def get_by_batch_id(
        self,
        batch_id: UUID,
    ) -> EmbeddingTask | None:
        pass

    @abstractmethod
    async def create(
        self,
        task: EmbeddingTask,
    ) -> EmbeddingTask:
        pass

    @abstractmethod
    async def update(
        self,
        task: EmbeddingTask,
    ) -> EmbeddingTask:
        pass

    @abstractmethod
    async def claim_ready(
        self,
        ingestion_job_id: UUID,
        *,
        limit: int,
        claimed_by: str,
        lease_until: datetime,
    ) -> list[EmbeddingTask]:
        pass

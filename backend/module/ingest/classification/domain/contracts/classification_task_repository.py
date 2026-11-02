from abc import ABC
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from module.ingest.classification.domain.entities.classification_task import (
    ClassificationTask,
)


class ClassificationLeaseLostError(RuntimeError):
    pass


class ClassificationTaskRepository(ABC):

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
    ) -> ClassificationTask | None:
        pass

    @abstractmethod
    async def get_by_batch_id(
        self,
        batch_id: UUID,
    ) -> ClassificationTask | None:
        pass

    @abstractmethod
    async def create(
        self,
        task: ClassificationTask,
    ) -> ClassificationTask:
        pass

    @abstractmethod
    async def update(
        self,
        task: ClassificationTask,
    ) -> ClassificationTask:
        pass

    @abstractmethod
    async def claim_ready(
        self,
        ingestion_job_id: UUID,
        *,
        limit: int,
        claimed_by: str,
        lease_until: datetime,
    ) -> list[ClassificationTask]:
        pass

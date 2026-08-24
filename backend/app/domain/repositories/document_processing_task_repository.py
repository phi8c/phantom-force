from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.document_processing_task import (
    DocumentProcessingTask,
)


class DocumentProcessingTaskRepository(
    ABC,
):

    @abstractmethod
    async def create(
        self,
        task: DocumentProcessingTask,
    ) -> DocumentProcessingTask:
        pass

    @abstractmethod
    async def get_pending_tasks(
        self,
        limit: int,
    ) -> list[DocumentProcessingTask]:
        pass

    @abstractmethod
    async def mark_running(
        self,
        task_id: UUID,
    ) -> None:
        pass

    @abstractmethod
    async def mark_completed(
        self,
        task_id: UUID,
    ) -> None:
        pass

    @abstractmethod
    async def mark_failed(
        self,
        task_id: UUID,
        error_message: str,
    ) -> None:
        pass
    @abstractmethod
    async def claim_pending_tasks(
        self,
        limit: int,
    ) -> list[DocumentProcessingTask]:
        pass
    
    @abstractmethod
    async def get_by_id(
        self,
        task_id: UUID,
    ) -> DocumentProcessingTask | None:
        pass
    
    


from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import select

from app.domain.entities.document_processing_task import (
    DocumentProcessingTask,
)

from app.domain.repositories.document_processing_task_repository import (
    DocumentProcessingTaskRepository,
)

from app.infrastructure.persistence.mappers.document_processing_task_mapper import (
    DocumentProcessingTaskMapper,
)

from app.infrastructure.persistence.models.document_processing_task import (
    DocumentProcessingTask as DocumentProcessingTaskModel,
)

from app.shared.repositories.base_repository import (
    BaseRepository,
)
from app.domain.enums.task_status import (
    TaskStatus,
)

class DocumentProcessingTaskRepositoryImpl(
    BaseRepository[
        DocumentProcessingTaskModel
    ],
    DocumentProcessingTaskRepository,
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=DocumentProcessingTaskModel,
        )

    async def create(
        self,
        task: DocumentProcessingTask,
    ) -> DocumentProcessingTask:

        model = (
            DocumentProcessingTaskMapper
            .to_model(
                task,
            )
        )

        created_model = await (
            self.add(
                model,
            )
        )

        return (
            DocumentProcessingTaskMapper
            .to_entity(
                created_model,
            )
        )
        
    async def get_pending_tasks(
        self,
        limit: int,
    ) -> list[DocumentProcessingTask]:

        stmt = (
            select(
                DocumentProcessingTaskModel,
            )
            .where(
                DocumentProcessingTaskModel.status
                == TaskStatus.PENDING
            )
            .limit(
                limit,
            )
        )

        result = await (
            self.session.execute(
                stmt,
            )
        )

        models = result.scalars().all()

        return [
            DocumentProcessingTaskMapper.to_entity(
                model,
            )
            for model in models
        ]
        
    async def get_pending_tasks(
        self,
        limit: int,
    ) -> list[DocumentProcessingTask]:

        stmt = (
            select(
                DocumentProcessingTaskModel,
            )
            .where(
                DocumentProcessingTaskModel.status
                == TaskStatus.PENDING
            )
            .limit(
                limit,
            )
        )

        result = await (
            self.session.execute(
                stmt,
            )
        )

        models = result.scalars().all()

        return [
            DocumentProcessingTaskMapper.to_entity(
                model,
            )
            for model in models
        ]
        
        
    async def mark_running(
        self,
        task_id: UUID,
    ) -> None:

        model = await super().get_by_id(
            task_id,
        )

        if not model:
            raise ValueError(
                "Task not found",
            )

        model.status = (
            TaskStatus.RUNNING
        )

        model.started_at = (
            datetime.now(
                timezone.utc,
            )
        )

        await self.session.flush()
        
    async def mark_completed(
        self,
        task_id: UUID,
    ) -> None:

        model = await super().get_by_id(
            task_id,
        )

        if not model:
            raise ValueError(
                "Task not found",
            )

        model.status = (
            TaskStatus.COMPLETED
        )

        model.finished_at = (
            datetime.now(
                timezone.utc,
            )
        )

        await self.session.flush()
        
    async def mark_failed(
        self,
        task_id: UUID,
        error_message: str,
    ) -> None:

        model = await super().get_by_id(
            task_id,
        )

        if not model:
            raise ValueError(
                "Task not found",
            )

        model.status = (
            TaskStatus.FAILED
        )

        model.error_message = (
            error_message
        )

        model.retry_count += 1

        model.finished_at = (
            datetime.now(
                timezone.utc,
            )
        )

        await self.session.flush()
    
    
    async def claim_pending_tasks(
        self,
        limit: int,
    ) -> list[DocumentProcessingTask]:

        stmt = (
            select(
                DocumentProcessingTaskModel,
            )
            .where(
                DocumentProcessingTaskModel.status
                == TaskStatus.PENDING
            )
            .order_by(
                DocumentProcessingTaskModel.created_at
            )
            .with_for_update(
                skip_locked=True,
            )
            .limit(
                limit,
            )
        )

        result = await (
            self.session.execute(
                stmt,
            )
        )

        models = result.scalars().all()

        now = datetime.now(
            timezone.utc,
        )

        for model in models:

            model.status = (
                TaskStatus.RUNNING
            )

            model.started_at = now

        await self.session.flush()

        return [
            DocumentProcessingTaskMapper.to_entity(
                model,
            )
            for model in models
        ]
    async def get_by_id(
        self, task_id: UUID
    ) -> DocumentProcessingTask | None:
        model = await super().get_by_id(
            task_id,
        )

        if not model:
            return None

        return DocumentProcessingTaskMapper.to_entity(
            model,
        )
        
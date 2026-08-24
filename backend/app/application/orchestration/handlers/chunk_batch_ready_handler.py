from app.application.orchestration.contracts.event_handler import (
    EventHandler,
)

from app.domain.events.chunk_batch_ready_event import ChunkBatchReadyEvent

from app.domain.entities.document_processing_task import (
    DocumentProcessingTask,
)

from app.domain.enums.task_status import TaskStatus
from app.domain.enums.task_type import TaskType

from app.domain.ports.messaging.message_bus import MessageBus

from app.domain.repositories.document_processing_task_repository import (
    DocumentProcessingTaskRepository,
)


class ChunkBatchReadyHandler(
    EventHandler[ChunkBatchReadyEvent],
):

    def __init__(
        self,
        task_repository: DocumentProcessingTaskRepository,
        message_bus: MessageBus,
    ) -> None:
        self._task_repository = task_repository
        self._message_bus = message_bus

    async def handle(
        self,
        event: ChunkBatchReadyEvent,
    ) -> None:

        await self._create_task(
            event=event,
            task_type=TaskType.CLASSIFICATION,
        )

        await self._create_task(
            event=event,
            task_type=TaskType.EMBEDDING,
        )

    async def _create_task(
        self,
        event: ChunkBatchReadyEvent,
        task_type: TaskType,
    ) -> None:

        task = DocumentProcessingTask(
            id=None,
            document_id=event.document_id,
            batch_id=event.batch_id,
            task_type=task_type.value,
            status=TaskStatus.PENDING.value,
            retry_count=0,
            error_message=None,
            started_at=None,
            finished_at=None,
            created_at=None,
            updated_at=None,
        )

        task = await self._task_repository.create(task)

        await self._message_bus.publish_task(
            task_id=str(task.id),
            task_type=task.task_type,
        )
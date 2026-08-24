from dataclasses import dataclass
from uuid import UUID

from app.domain.enums.task_type import (
    TaskType,
)

from app.domain.events.base_event import (
    BaseEvent,
)


@dataclass
class BatchCompletedEvent(
    BaseEvent,
):

    document_id: UUID

    batch_id: UUID

    task_id: UUID

    pipeline: TaskType
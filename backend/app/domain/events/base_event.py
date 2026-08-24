# app/domain/events/base_event.py

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from uuid import uuid4
from datetime import timezone


@dataclass(slots=True)
class BaseEvent:

    event_id: UUID
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        **kwargs,
    ):
        return cls(
            event_id=uuid4(),
            occurred_at=datetime.now(timezone.utc),
            **kwargs,
        )
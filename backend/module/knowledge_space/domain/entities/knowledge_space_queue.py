from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .queue_provider import QueueProvider


@dataclass(frozen=True, slots=True)
class KnowledgeSpaceQueue:
    id: UUID
    knowledge_space_id: UUID
    queue_provider_id: UUID
    configuration: dict
    is_default: bool
    enabled: bool
    created_at: datetime | None
    updated_at: datetime | None
    provider: QueueProvider | None

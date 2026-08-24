from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class SyncState:
    id: UUID

    source_id: UUID

    delta_token: str | None

    last_sync_at: datetime | None

    created_at: datetime

    updated_at: datetime
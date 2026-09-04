from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ModelSet:

    id: UUID | None

    feature_id: UUID

    code: str

    name: str

    description: str | None

    enabled: bool

    created_at: datetime | None

    updated_at: datetime | None

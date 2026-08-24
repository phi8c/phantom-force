from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Enterprise:

    id: UUID | None

    code: str

    name: str

    description: str | None

    status: str

    created_at: datetime | None

    updated_at: datetime | None
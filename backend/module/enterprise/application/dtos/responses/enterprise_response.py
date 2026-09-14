from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class EnterpriseResponse:
    id: UUID
    code: str
    name: str
    description: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None

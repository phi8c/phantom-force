from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class KnowledgeSpaceListItem:

    id: UUID

    enterprise_id: UUID

    enterprise_name: str

    name: str

    code: str

    description: str | None

    status: str

    created_at: datetime | None

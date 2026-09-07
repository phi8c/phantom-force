from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AIProvider:

    id: UUID | None

    code: str

    name: str

    provider_type: str

    base_url: str | None

    api_version: str | None

    description: str | None

    is_enabled: bool

    created_at: datetime | None

    updated_at: datetime | None

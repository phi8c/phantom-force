from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DataHubProvider:

    id: UUID | None

    code: str

    name: str

    provider: str

    configuration_schema: dict

    enabled: bool

    created_at: datetime | None

    updated_at: datetime | None
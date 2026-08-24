from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ExtractionStrategy:

    id: UUID | None

    code: str

    name: str

    provider: str

    configuration: dict

    enabled: bool

    created_at: datetime | None

    updated_at: datetime | None
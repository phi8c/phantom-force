from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Prompt:

    id: UUID | None

    code: str

    name: str | None

    description: str | None

    system_prompt: str

    configuration: dict

    enabled: bool

    created_at: datetime | None

    updated_at: datetime | None

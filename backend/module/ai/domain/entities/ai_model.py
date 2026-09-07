from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AIModel:

    id: UUID | None

    provider_id: UUID

    code: str

    display_name: str

    model_type: str

    context_window: int | None

    max_output_tokens: int | None

    supports_stream: bool

    supports_json: bool

    supports_vision: bool

    supports_tools: bool

    description: str | None

    is_enabled: bool

    created_at: datetime | None

    updated_at: datetime | None

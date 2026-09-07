from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResult:

    content: str | None

    provider_code: str

    model_code: str

    response_id: str | None

    finish_reason: str | None

    usage: dict[str, Any]

from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass(frozen=True)
class ChatResponse:
    answer: str

    intent: str | None = None

    knowledge_requests: list[dict[str, Any]] = field(
        default_factory=list,
    )

    information: list[dict[str, Any]] = field(
        default_factory=list,
    )

    @property
    def seeds(self) -> list[dict[str, Any]]:
        return self.knowledge_requests

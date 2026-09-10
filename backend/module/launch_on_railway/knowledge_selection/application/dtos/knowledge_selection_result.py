from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass(frozen=True)
class KnowledgeSelection:
    request_id: str
    information_type_codes: list[str] = field(default_factory=list)
    topic_codes: list[str] = field(default_factory=list)
    field_codes: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)

    @property
    def seed_id(self) -> str:
        return self.request_id


@dataclass(frozen=True)
class KnowledgeSelectionResult:
    selections: list[KnowledgeSelection] = field(default_factory=list)
    raw_response: dict[str, Any] = field(default_factory=dict)

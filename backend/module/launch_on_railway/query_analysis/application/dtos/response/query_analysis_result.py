from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass(frozen=True)
class QuerySeed:
    object_code: str | None = None
    identifier_code: str | None = None
    information_type_code: str | None = None
    topic_codes: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None


@dataclass(frozen=True)
class QueryAnalysisResult:
    intent: str
    seeds: list[QuerySeed]
    raw_response: dict[str, Any]

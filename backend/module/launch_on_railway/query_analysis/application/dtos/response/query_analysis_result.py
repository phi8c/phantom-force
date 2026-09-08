from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QueryAnalysisResult:
    intent: str
    seeds: list[dict[str, Any]]
    raw_response: dict[str, Any]
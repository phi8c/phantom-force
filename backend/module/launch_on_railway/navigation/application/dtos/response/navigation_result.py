from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NavigationItem:
    information_id: str
    summary: str
    data: dict[str, Any] | None = None
    source_refs: list[dict[str, Any]] = field(default_factory=list)
    confidence: float | None = None


@dataclass(frozen=True)
class NavigationResult:
    items: list[NavigationItem] = field(default_factory=list)

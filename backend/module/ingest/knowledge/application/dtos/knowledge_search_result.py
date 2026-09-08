from dataclasses import dataclass
from dataclasses import field
from typing import Any
from uuid import UUID


@dataclass
class KnowledgeSearchItem:
    information_id: UUID
    information_type_code: str | None
    summary: str
    data: dict[str, Any] | None = None
    object_refs: list[dict[str, Any]] = field(default_factory=list)
    topic_refs: list[dict[str, Any]] = field(default_factory=list)
    source_refs: list[dict[str, Any]] = field(default_factory=list)
    confidence: float | None = None


@dataclass
class KnowledgeSearchResult:
    items: list[KnowledgeSearchItem] = field(default_factory=list)

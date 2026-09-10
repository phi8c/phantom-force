from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass(frozen=True)
class KnowledgeRequest:
    need: str
    document_type_seeds: list[str] = field(default_factory=list)
    head_seeds: list[str] = field(default_factory=list)
    topic_seeds: list[str] = field(default_factory=list)
    object_seeds: list[str] = field(default_factory=list)
    identifier_seeds: list[str] = field(default_factory=list)
    information_type_seeds: list[str] = field(default_factory=list)
    information_field_seeds: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None

    @property
    def object_code(self) -> str | None:
        return self.object_seeds[0] if self.object_seeds else None

    @property
    def identifier_code(self) -> str | None:
        return (
            self.identifier_seeds[0]
            if self.identifier_seeds
            else None
        )

    @property
    def information_type_code(self) -> str | None:
        return (
            self.information_type_seeds[0]
            if self.information_type_seeds
            else None
        )

    @property
    def topic_codes(self) -> list[str]:
        return self.topic_seeds


@dataclass(frozen=True)
class QueryAnalysisResult:
    intent: str
    knowledge_requests: list[KnowledgeRequest]
    raw_response: dict[str, Any]

    @property
    def seeds(self) -> list[KnowledgeRequest]:
        return self.knowledge_requests

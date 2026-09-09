from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass(frozen=True)
class KnowledgeDocumentTypeContext:
    code: str
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeTopicContext:
    code: str
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeHeadContext:
    type: str | None = None
    code: str | None = None
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeDocumentContext:
    document_type: KnowledgeDocumentTypeContext
    topics: list[KnowledgeTopicContext] = field(default_factory=list)
    head: KnowledgeHeadContext = field(default_factory=KnowledgeHeadContext)

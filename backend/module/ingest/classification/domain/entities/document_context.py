from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass(frozen=True)
class DocumentContextDocumentType:
    code: str
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentContextTopic:
    code: str
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentContextHead:
    type: str | None = None
    code: str | None = None
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentContext:
    document_type: DocumentContextDocumentType
    topic: DocumentContextTopic
    head: DocumentContextHead

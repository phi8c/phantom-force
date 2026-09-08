from dataclasses import dataclass
from dataclasses import field
from typing import Any
from uuid import UUID


@dataclass
class KnowledgeSearchRequest:
    knowledge_space_id: UUID
    object_code: str
    identifier_code: str | None = None
    information_type_code: str | None = None
    topic_codes: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeSpaceOidcStartRequest:
    knowledge_space_id: UUID

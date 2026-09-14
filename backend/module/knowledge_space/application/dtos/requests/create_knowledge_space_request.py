from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateKnowledgeSpaceRequest:
    enterprise_id: UUID
    name: str
    code: str
    description: str | None = None
    configuration: dict | None = None

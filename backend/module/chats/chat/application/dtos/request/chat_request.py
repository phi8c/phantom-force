from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ChatRequest:
    knowledge_space_id: UUID
    question: str
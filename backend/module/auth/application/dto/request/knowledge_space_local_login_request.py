from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeSpaceLocalLoginRequest:
    knowledge_space_id: UUID
    email: str
    password: str
    ip_address: str | None
    user_agent: str | None
    device_fingerprint: str | None

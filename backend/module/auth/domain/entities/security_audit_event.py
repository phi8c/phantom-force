from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class SecurityAuditEvent:
    id: UUID
    actor_user_id: UUID | None
    action: str
    target_type: str | None
    target_id: UUID | None
    ip_address: str | None
    user_agent: str | None
    device_fingerprint: str | None
    metadata: dict[str, Any] | None
    occurred_at: datetime

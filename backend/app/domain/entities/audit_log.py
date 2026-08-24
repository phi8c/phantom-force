from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class AuditLog:

    id: str

    actor_user_id: str | None

    action: str

    target_type: str | None

    target_id: str | None

    ip_address: str | None

    user_agent: str | None

    device_fingerprint: str | None

    metadata: dict[str, Any] | None

    occurred_at: datetime
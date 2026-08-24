from dataclasses import dataclass
from datetime import datetime

from app.domain.enums.auth_provider import AuthProvider


@dataclass
class AuthSession:

    id: str

    user_id: str

    session_token_hash: str

    auth_method: AuthProvider

    ip_address: str | None

    user_agent: str | None

    device_fingerprint: str | None

    issued_at: datetime

    last_seen_at: datetime

    idle_expires_at: datetime

    absolute_expires_at: datetime

    revoked_at: datetime | None

    revoked_reason: str | None
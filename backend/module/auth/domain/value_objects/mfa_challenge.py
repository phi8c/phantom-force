from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)


@dataclass(frozen=True)
class MfaChallenge:
    user_id: UUID
    auth_method: AuthProvider
    context_type: AuthenticationContextType
    knowledge_space_id: UUID | None
    idle_timeout_minutes: int
    absolute_timeout_minutes: int
    ip_address: str | None
    user_agent: str | None
    device_fingerprint: str | None
    created_at: datetime
    expires_at: datetime
    identity_link_id: UUID | None = None

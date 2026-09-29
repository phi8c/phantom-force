from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.services.auth_policy_validation import validate_auth_policy


@dataclass
class ManagementAuthPolicy:
    id: UUID
    auth_method: AuthProvider
    tenant_id: str | None
    require_mfa: bool
    idle_timeout_minutes: int
    absolute_timeout_minutes: int
    reauthentication_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        validate_auth_policy(
            auth_method=self.auth_method,
            tenant_id=self.tenant_id,
            idle_timeout_minutes=self.idle_timeout_minutes,
            absolute_timeout_minutes=self.absolute_timeout_minutes,
        )
        if not 0 < self.reauthentication_minutes <= self.absolute_timeout_minutes:
            raise ValueError(
                "Reauthentication timeout must be positive and cannot exceed absolute timeout"
            )

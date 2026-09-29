from dataclasses import dataclass
from uuid import UUID

from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)


@dataclass(frozen=True)
class ResolvedAuthPolicy:
    context_type: AuthenticationContextType
    knowledge_space_id: UUID | None
    auth_method: AuthProvider
    tenant_id: str | None
    require_mfa: bool
    idle_timeout_minutes: int
    absolute_timeout_minutes: int
    reauthentication_minutes: int | None

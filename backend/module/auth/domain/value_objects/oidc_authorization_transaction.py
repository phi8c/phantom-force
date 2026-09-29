from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)


@dataclass(frozen=True)
class OidcAuthorizationTransaction:
    context_type: AuthenticationContextType
    knowledge_space_id: UUID | None
    expected_tenant_id: str
    nonce: str
    code_verifier: str
    require_mfa: bool
    idle_timeout_minutes: int
    absolute_timeout_minutes: int
    created_at: datetime
    expires_at: datetime

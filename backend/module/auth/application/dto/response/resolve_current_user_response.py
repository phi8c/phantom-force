from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)


@dataclass(frozen=True)
class ResolveCurrentUserResult:
    user_id: UUID
    email: str
    session_id: UUID
    auth_method: AuthProvider
    context_type: AuthenticationContextType
    knowledge_space_id: UUID | None
    authenticated_at: datetime
    mfa_verified_at: datetime | None

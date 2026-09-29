from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.auth.domain.enums.auth_provider import AuthProvider


@dataclass
class IdentityLink:

    id: UUID

    user_id: UUID

    provider: AuthProvider

    external_sub: str

    tenant_id: str | None

    email_at_link: str

    linked_at: datetime

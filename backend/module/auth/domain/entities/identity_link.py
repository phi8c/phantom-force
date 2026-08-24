from dataclasses import dataclass
from datetime import datetime

from module.auth.domain.enums.auth_provider import AuthProvider


@dataclass
class IdentityLink:

    id: str

    user_id: str

    provider: AuthProvider

    external_sub: str

    tenant_id: str | None

    email_at_link: str

    linked_at: datetime
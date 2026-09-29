from dataclasses import dataclass

from module.auth.domain.enums.auth_provider import AuthProvider


@dataclass(frozen=True)
class KnowledgeSpaceAuthRequirement:
    auth_method: AuthProvider
    require_mfa: bool

from dataclasses import dataclass


@dataclass(frozen=True)
class OidcUserInfo:
    external_sub: str
    email: str
    email_verified: bool
    tenant_id: str

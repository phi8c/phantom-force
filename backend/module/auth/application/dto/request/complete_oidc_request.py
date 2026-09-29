from dataclasses import dataclass


@dataclass(frozen=True)
class CompleteOidcRequest:
    state: str
    code: str
    ip_address: str | None = None
    user_agent: str | None = None
    device_fingerprint: str | None = None

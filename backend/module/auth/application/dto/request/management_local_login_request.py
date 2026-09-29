from dataclasses import dataclass


@dataclass(frozen=True)
class ManagementLocalLoginRequest:
    email: str
    password: str
    ip_address: str | None
    user_agent: str | None
    device_fingerprint: str | None

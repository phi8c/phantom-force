from dataclasses import dataclass


@dataclass
class LocalLoginRequest:

    email: str

    password: str

    ip_address: str | None

    user_agent: str | None

    device_fingerprint: str | None
    

from dataclasses import dataclass


@dataclass(frozen=True)
class VerifyEmailRequest:
    raw_token: str

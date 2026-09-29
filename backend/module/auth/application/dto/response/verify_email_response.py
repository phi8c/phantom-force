from dataclasses import dataclass


@dataclass(frozen=True)
class VerifyEmailResult:
    message: str

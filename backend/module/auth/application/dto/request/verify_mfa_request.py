from dataclasses import dataclass


@dataclass(frozen=True)
class VerifyMfaRequest:
    challenge_id: str
    code: str

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LocalLoginResult:
    status: Literal[
        "success",
        "mfa_required",
        "mfa_enrollment_required",
    ]
    session_token: str | None = None
    mfa_challenge_id: str | None = None

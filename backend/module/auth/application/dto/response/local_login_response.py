
from typing import Literal

from dataclasses import dataclass
@dataclass
class LocalLoginResult:

    status: Literal[
        "success",
        "mfa_required",
    ]

    session_token: str | None = None

    mfa_challenge_id: str | None = None
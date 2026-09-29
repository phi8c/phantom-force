from dataclasses import dataclass


@dataclass(frozen=True)
class ResolveCurrentUserRequest:
    raw_session_token: str

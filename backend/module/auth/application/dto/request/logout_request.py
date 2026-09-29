from dataclasses import dataclass


@dataclass(frozen=True)
class LogoutRequest:
    raw_session_token: str

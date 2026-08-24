from dataclasses import dataclass

@dataclass
class ResolveCurrentUserRequest:

    raw_session_token: str
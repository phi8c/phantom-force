from dataclasses import dataclass


@dataclass
class LogoutRequest:
 
    raw_session_token: str
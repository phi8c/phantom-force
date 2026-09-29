from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterLocalUserRequest:
    email: str
    password: str

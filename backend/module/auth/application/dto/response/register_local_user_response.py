from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterLocalUserResult:
    message: str
